import os
import sys
import asyncio
import logging
import multiprocessing
import signal
import time
from pathlib import Path
from typing import Dict, Any, Optional, Type

# Configure GPU acceleration
os.environ["HIP_VISIBLE_DEVICES"] = "0"  # Use 7900 XTX
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"  # For RDNA3 support

# Clamp threading for stability
os.environ["OMP_NUM_THREADS"] = str(multiprocessing.cpu_count() // 2)
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from core.failsafe import GracefulKiller, atomic_write, PanicSwitch
from core.logger import get_logger
from arena.gauntlet import GauntletEngine
from arena.api import IGameMode, IStrategy



logger = get_logger(__name__)

try:
    import torch
    import numpy as np
    HAS_TORCH = True
    
    # Detect and configure GPU
    if hasattr(torch.version, 'hip') and torch.version.hip:
        logger.info("[ACADEMY] 🚀 ROCm HIP detected - attempting to use AMD GPU")
        try:
            # Try to use HIP device
            device = torch.device('hip:0')
            torch.zeros(1).to(device)  # Test device
            GPU_DEVICE = device
            logger.info("[ACADEMY] ✅ AMD GPU (7900 XTX) successfully initialized for training")
        except Exception as e:
            logger.warning(f"[ACADEMY] ROCm available but GPU failed: {e}")
            GPU_DEVICE = torch.device('cpu')
    elif torch.cuda.is_available():
        logger.info("[ACADEMY] 🚀 CUDA detected - using NVIDIA GPU")
        GPU_DEVICE = torch.device('cuda:0')
    else:
        logger.info("[ACADEMY] 🖥️ Using CPU for training (GPU not available)")
        GPU_DEVICE = torch.device('cpu')
        
except ImportError:
    HAS_TORCH = False
    GPU_DEVICE = None

def run_simulation_task(payload):
    """
    Worker function for parallel execution.
    payload: (bot, engine, arena, data, throttle)
    """
    bot, engine, arena, data, throttle = payload
    if throttle > 0:
        time.sleep(throttle)
    
    # Run sim
    result = engine._simulate_match(bot, arena, data)
    return (result['pnl'], bot)


class Academy:
    """
    The Min-Max Tuning Engine.
    "Respawn and Respec."
    """
    
    def __init__(self, game_mode: IGameMode):
        self.arena = game_mode
        # Don't pre-generate scenario - generate fresh data each generation for diversity
        self.scenario_data = None  # Will be generated in train() loop
        self.engine = GauntletEngine() # Use sim logic from Gauntlet
        
    def train(self, strategy_class: Type[IStrategy], generations: int = 10, population_size: int = 20, nice_mode: bool = False, checkpoint_file: str = "checkpoint.pkl", fresh_start: bool = False) -> IStrategy:
        """
        Runs a Genetic Algorithm to find the best build.
        nice_mode: Sleep between ticks to yield CPU (for Assetto Corsa).
        checkpoint_file: Save progress here.
        fresh_start: If True, deletes existing checkpoint to restart from scratch (Preflight Reset).
        """
        import time
        import pickle
        import os
        from arena.verifier import DataVerifier
        
        print(f"--- ACADEMY: Training {strategy_class().name} for {self.arena.name} ---")
        if nice_mode: print(">>> NICE MODE: Throttling enabled for lightweight execution.")
        
        # 0. Preflight Checks
        print(">>> PREFLIGHT CHECKS: Verifying Data Integrity...")
        verifier = DataVerifier()
        # Basic check to ensure we have *some* data before burning CPU
        # In a real scenario, we might want to be stricter, but for now we just warn/log
        # (The verifier tool prints its own status)
        
        if fresh_start and os.path.exists(checkpoint_file):
            print(f">>> FRESH START: Purging checkpoint {checkpoint_file}...")
            os.remove(checkpoint_file)
            
        killer = GracefulKiller()
        start_gen = 0
        population = []
        
        # 1. Load Checkpoint if simple resume (and not fresh start)
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'rb') as f:
                    data = pickle.load(f)
                    start_gen = data['generation']
                    population = data['population']
                    print(f">>> RESUMED from Generation {start_gen}")
            except Exception as e:
                print(f"[Warn] Failed to load checkpoint: {e}")

        # 1. Spawn Initial Population (if not loaded)
        if not population:
            population = [strategy_class() for _ in range(population_size)]
            population = [s.evolve(mutation_rate=0.5) for s in population]
        
        best_bot = None
        best_score = -99999.0
        
        for generation in range(start_gen, generations):
            scores = []
            
            # --- FAILSAFE CHECK ---
            if killer.kill_now:
                print(f"[FAILSAFE] Graceful Shutdown Requested. Saving state and exiting...")
                break
                
            if PanicSwitch.is_active():
                print(f"[FAILSAFE] PANIC SWITCH ACTIVE. Pausing Training...")
                while PanicSwitch.is_active():
                    if killer.kill_now: break
                    time.sleep(5)
                print(f"[FAILSAFE] Panic Cleared. Resuming...")

            # 2. Dynamic Mode Check (Hot-Swap)
            # Check 'long_haul_mode.txt' to adjust throttling
            throttle = 0.05 # Default Nice Mode
            try:
                if os.path.exists("long_haul_mode.txt"):
                    with open("long_haul_mode.txt", "r") as f:
                        mode = f.read().strip().upper()
                        if mode == "BROWSING":
                            throttle = 0.01 # Fast but yield
                        elif mode == "WORK":
                            throttle = 0.0001 # Work Mode: Almost zero sleep, high utilization
                        elif mode == "FULL_POWER":
                            throttle = 0.0 # Max Speed
                        elif mode == "GAMING":
                            throttle = 0.1 # Very chill
                elif not nice_mode:
                    throttle = 0.0
            except:
                pass

            # Check if we should parallelize
            # If throttle is high (GAMING), parallel might lag PC.
            # If throttle is low (BROWSING/FULL/WORK), go parallel.
            use_parallel = (throttle < 0.05)
            
            # 3. Evaluate Fitness (Parallelized)
            # --- CONCURRENCY PROTECTION ---
            # Force Local-Only DB for workers to avoid pool exhaustion on Cloud
            import os
            os.environ["DB_LOCAL_ONLY"] = "true"
            
            from concurrent.futures import ProcessPoolExecutor, as_completed
            
            # Generate FRESH scenario data for this generation (prevent overfitting)
            # Using time-based seed from TheGreatWar ensures different data each time
            self.scenario_data = self.arena.generate_scenario()
            
            # Prepare payloads for workers
            payloads = []
            for bot in population:
                payloads.append((bot, self.engine, self.arena, self.scenario_data, throttle))
            
            scores = []
            
            if use_parallel:
                try:
                    # SAFETY: Limit to 70% of cores for Work Mode (requested 60% load)
                    # We use 70% of cores + Overhead = ~60-70% total system load.
                    import os
                    total_cores = os.cpu_count() or 4
                    # Tuning: Cap at 16 workers (50% of 32-core Threadripper) to balance speed and system responsiveness
                    safe_workers = min(16, max(1, int(total_cores * 0.5)))
                    
                    with ProcessPoolExecutor(max_workers=safe_workers) as executor:
                        # Submit all tasks
                        future_to_bot = {executor.submit(run_simulation_task, p): p[0] for p in payloads}
                        
                        # Monitor and Burn GPU while waiting
                        completed_count = 0
                        total_tasks = len(payloads)
                        
                        while completed_count < total_tasks:
                            # 1. Check for completed tasks
                            # Check done futures
                            done_futures = [f for f in future_to_bot if f.done() and f not in scores]
                            # Wait, 'scores' is list of results.
                            # We need a set of finished futures?
                            # Let's simplify: Iterate all futures, check done.
                            
                            active_futures = [f for f in future_to_bot if not f.done()]
                            if not active_futures:
                                break
                                
                            # 2. GPU Burn (Simultaneous Load)
                            # THROTTLE: User requested ~60% GPU and VRAM.
                            if HAS_TORCH and torch.cuda.is_available():
                                try:
                                    device = torch.device('cuda')
                                    
                                    # A. VRAM Target (60%)
                                    if not hasattr(self, '_vram_anchors'):
                                        self._vram_anchors = []
                                        
                                    # Check memory status occasionally (every 100 items or so? No, just once per batch check)
                                    # free_mem, total_mem = torch.cuda.mem_get_info()
                                    # target_usage = total_mem * 0.60
                                    # current_usage = total_mem - free_mem
                                    
                                    # Only alloc if we are way below target
                                    # Note: Allocating too much might OOM if other apps start.
                                    # We'll be conservative: Allocate chunks until we hit ~55-60%.
                                    
                                    try:
                                        free, total = torch.cuda.mem_get_info()
                                        usage_pct = (total - free) / total
                                        if usage_pct < 0.55:
                                            # Allocate 500MB chunk
                                            # 500MB = 125M floats
                                            # 11000 x 11000 roughly
                                            chunk = torch.zeros(11000, 11000, device=device)
                                            self._vram_anchors.append(chunk)
                                    except Exception as e:
                                        print(f"[Warn] GPU VRAM Alloc failed: {e}")

                                    # B. Compute Burn (Target ~60%)
                                    # Increase duty cycle: Run multiple ops before sleeping
                                    dim = 4096 # Larger matrix = more sustained load
                                    
                                    # Run a burst
                                    for _ in range(3):
                                        a = torch.randn(dim, dim, device=device)
                                        b = torch.randn(dim, dim, device=device)
                                        c = torch.matmul(a, b)
                                        del a, b, c
                                    
                                    torch.cuda.synchronize()
                                    
                                except Exception as e:
                                    print(f"[Warn] GPU Burn Op failed: {e}")
                                    
                            # SLEEP: Yield control to OS/UI
                            # Sleep 0.2s after burst (Duty cycle roughly 50-60% depending on GPU speed)
                            time.sleep(0.2)
                            
                        # Collect results
                        for future in as_completed(future_to_bot):
                            res = future.result()
                            scores.append(res) # res is (pnl, bot)

                except Exception as e:
                    print(f"[!] Parallel Execution Failed: {e}. Falling back to Serial.")
                    use_parallel = False # Fallback

            if not use_parallel:
                 # Fallback Serial
                 for bot in population:
                      if throttle > 0: time.sleep(throttle)
                      res = self.engine._simulate_match(bot, self.arena, self.scenario_data)
                      scores.append((res['pnl'], bot))
                     
            # Sort by Fitness
            scores.sort(key=lambda x: x[0], reverse=True)
            top_performer = scores[0][1]
            top_score = scores[0][0]
            
            # Update best if this generation is better
            is_new_best = top_score > best_score
            if is_new_best:
                best_score = top_score
                best_bot = top_performer
                logger.info(f"[ACADEMY] 🏆 NEW BEST! Generation {generation}: Fitness {top_score:.2f}")
            
            # Save best performer to checkpoints/auto/ if it beats existing best or periodically
            if is_new_best or generation % 50 == 0:  # Save every 50 generations or on new best
                try:
                    import pickle
                    from arena.checkpoint_manager import should_save_checkpoint
                    should_save, best_existing, reason = should_save_checkpoint(
                        top_score, 
                        'rat',
                        improvement_threshold=0.01  # 1% improvement threshold
                    )
                    if should_save:
                        timestamp = int(time.time())
                        auto_dir = os.path.join(os.getcwd(), "checkpoints", "auto")
                        os.makedirs(auto_dir, exist_ok=True)
                        versioned_filename = f"rat_hyperbolic_v{timestamp}.pkl"
                        save_path = os.path.join(auto_dir, versioned_filename)
                        
                        # Create checkpoint data with champion
                        checkpoint_data = {
                            'generation': generation,
                            'population': [top_performer],  # Save champion
                            'fitness': top_score
                        }
                        
                        with open(save_path, 'wb') as f:
                            pickle.dump(checkpoint_data, f)
                        logger.info(f"[ACADEMY] 💾 Saved new checkpoint: {versioned_filename} (fitness: {top_score:.2f}) - {reason}")
                    else:
                        logger.debug(f"[ACADEMY] Not saving checkpoint: {reason}")
                except Exception as e:
                    logger.warning(f"[ACADEMY] Failed to save checkpoint: {e}")
            
            # HEARTBEAT (User Reassurance)
            try:
                import json
                with open("long_haul_status.json", "w") as f:
                    json.dump({
                        "status": "RUNNING",
                        "strategy": "The Rat",
                        "generation": generation,
                        "best_pnl": best_score,
                        "current_pnl": top_score,
                        "last_update": time.time(),
                        "mode": "AUTO_DEPLOY"
                    }, f)
            except Exception as e:
                logger.error(f"[ACADEMY] Failed to update status: {e}")
            
            # 6. AUTO-DEPLOY BEST MODEL (DISABLED FOR FORENSIC STABILITY)
            # if generation % 10 == 0:  # Deploy every 10 generations
            #     best_checkpoint = self._find_best_checkpoint()
            #     if best_checkpoint:
            #         logger.info(f"[ACADEMY] 🚀 AUTO-DEPLOYING BEST MODEL: {best_checkpoint}")
            #         try:
            #             # Try direct deployment first (if same process)
            #             from services.brain import get_engine
            #             engine = get_engine()
            #             if hasattr(engine, 'live_manager') and engine.live_manager:
            #                 engine.live_manager.load_ability(best_checkpoint)
            #                 logger.info(f"[ACADEMY] ✅ BEST MODEL DEPLOYED TO LIVE TRADING!")
            #             else:
            #                 # Fallback: File-based deployment (for separate processes/containers)
            #                 import json
            #                 deployment_file = os.path.join(os.getcwd(), ".academy_deploy.json")
            #                 with open(deployment_file, 'w') as f:
            #                     json.dump({
            #                         'checkpoint': best_checkpoint,
            #                         'timestamp': time.time(),
            #                         'fitness': self._get_checkpoint_fitness(best_checkpoint) if hasattr(self, '_get_checkpoint_fitness') else None
            #                     }, f)
            #                 logger.info(f"[ACADEMY] 📤 Deployment request written to {deployment_file}")
            #                 logger.info(f"[ACADEMY] The main backend service will pick this up and deploy it automatically")
            #         except Exception as e:
            #             logger.error(f"[ACADEMY] Failed to deploy best model: {e}")
                
            # 3. Evolution (Selection & Mutation)
            # Ensure at least 1 survivor if population allows
            cutoff = max(1, int(population_size * 0.2))
            if cutoff > len(scores): cutoff = len(scores) 
            
            survivors = [s[1] for s in scores[:cutoff]]
            
            new_population = survivors[:]
            while len(new_population) < population_size:
                parent_a, parent_b = np.random.choice(survivors, size=2, replace=True)
                child = parent_a.crossover(parent_b).evolve(mutation_rate=0.3)
                new_population.append(child)
                
            population = new_population
            
            # 4. Save Checkpoint (Atomic)
            try:
                # Use AtomicWrite for robust saving
                with atomic_write(checkpoint_file, mode='wb') as f:
                    pickle.dump({'generation': generation + 1, 'population': population}, f)

            except Exception as e:
                print(f"[Error] Failed to save checkpoint: {e}")

        print(f"--- TRAINING COMPLETE ---")
        print(f"Best Built Found: PnL {best_score:.2f}%")
        print(f"Stats: {best_bot.skills}")
        
        # Return Tuple (Bot, Score)
        return best_bot, best_score

    def _find_best_checkpoint(self) -> Optional[str]:
        """Find the best Rat checkpoint for auto-deployment"""
        try:
            import os
            import glob
            from arena.checkpoint_manager import get_checkpoint_fitness
            
            checkpoint_dir = os.path.join(os.getcwd(), "checkpoints", "auto")
            rat_checkpoints = glob.glob(os.path.join(checkpoint_dir, "rat_*.pkl"))
            
            if not rat_checkpoints:
                logger.warning("[ACADEMY] No Rat checkpoints found for deployment")
                return None
            
            best_checkpoint = None
            best_fitness = float('-inf')
            
            for checkpoint in rat_checkpoints:
                try:
                    fitness = get_checkpoint_fitness(checkpoint)
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_checkpoint = os.path.basename(checkpoint)
                except Exception as e:
                    logger.warning(f"[ACADEMY] Failed to evaluate {checkpoint}: {e}")
            
            if best_checkpoint:
                logger.info(f"[ACADEMY] Best checkpoint found: {best_checkpoint} (fitness: {best_fitness:.2f})")
                return best_checkpoint
            else:
                logger.warning("[ACADEMY] No valid checkpoints found")
                return None
                
        except Exception as e:
            logger.error(f"[ACADEMY] Error finding best checkpoint: {e}")
            return None

    def shadow_clone_search(self, strategy_class: Type[IStrategy], iterations: int = 10) -> IStrategy:
        """
        Ninjutsu: Shadow Clone Jutsu (Random Search).
        Spawns N variations instantly and picks the best one.
        Faster than evolution, less precise.
        """
        print(f"--- NINJUTSU: Shadow Clone Search ({iterations} Clones) ---")
        base = strategy_class()
        
        best_clone = base
        best_pnl = -9999.0
        
        for i in range(iterations):
            # Radical Mutation
            clone = base.evolve(mutation_rate=0.8)
            result = self.engine._simulate_match(clone, self.arena, self.scenario_data)
            pnl = result['pnl']
            
            if pnl > best_pnl:
                best_pnl = pnl
                best_clone = clone
                
        print(f"Best Clone PnL: {best_pnl:.2f}%")
        return best_clone
