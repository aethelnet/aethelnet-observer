from .base import IPlugin
import os
import random
import psutil
import platform


class GovernorPlugin(IPlugin):
    """
    The Governor V4 (The Gamer).
    Features:
    - Gaming Detection: Yields 99% resources when Steam/Games are running.
    - Battery Awareness (Eco Mode).
    - Architecture Detection (ARM/Deck).
    """
    def __init__(self):
        self.mode = "DEFAULT"
        self.cpu_count = psutil.cpu_count(logical=False) or 4
        self.total_ram_gb = psutil.virtual_memory().total / (1024**3)
        self.arch = platform.machine().lower()
        self.node = platform.node().lower()
        self.is_gaming = False
        self.process = psutil.Process()
        
        print(f"[Governor] Hardware: {self.cpu_count} phys cores | {self.total_ram_gb:.1f} GB RAM | Arch: {self.arch}")

    @property
    def name(self) -> str:
        return "The Governor V4"

    def on_cycle_start(self, cycle_num: int):
        # Re-check environment every cycle (cheap check)
        self.check_environment()

    def check_environment(self):
        # 1. Gaming Detection
        # Scan for heavy graphical processes or Steam games
        # Heavy keywords: 'steam_app', 'acs.exe' (Assetto), 'BeamNG', 'vulkan', 'gamescope' (Deck UI)
        # We check this periodically, not every millisecond.
        
        # On Steam Deck, 'gamescope' is always running, so we look for 'steam_app' (Game)
        keywords = ['steam_app', 'acs.exe', 'BeamNG', 'Cyberpunk', 'Elden', 'Forza', 'vulkan']
        
        found_game = False
        try:
            # Quick scan of top CPU/Memory processes might be faster than iterating all
            # But iterating all is safer. Limit to processes with significant CPU?
            # Let's simple-scan the names.
            for proc in psutil.process_iter(['name']):
                try:
                    p_name = proc.info['name']
                    if p_name and any(k in p_name for k in keywords):
                        found_game = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                     continue
        except:
             pass
             
        self.is_gaming = found_game
        if self.is_gaming:
            # Set THIS process to lowest priority (IDLE)
            try:
                # Linux: 19 (Lowest priority)
                self.process.nice(19) 
            except:
                pass

    def get_resource_constraints(self) -> dict:
        # 1. LIVE TRADING Priority
        if os.path.exists("LIVE_TRADING_ACTIVE"):
             return {"population_size": 2, "throttle": 1.0, "parallel": False}
             
        # 2. GAMING MODE (Critical for User Experience)
        if self.is_gaming:
            # print("[Governor] 🎮 GAMING DETECTED. YIELDING RESOURCES.") 
            # Silent yield to avoid log spam, but Aggressive Yield
            return {
                "population_size": 2,      # Single pair
                "throttle": 5.0,           # Huge sleep between generations
                "parallel": False          # Single Thread
            }
             
        # 3. BATTERY ECO MODE
        battery = psutil.sensors_battery()
        if battery is not None and not battery.power_plugged:
            return {
                "population_size": max(2, int(self.cpu_count)), 
                "throttle": 1.0, 
                "parallel": True 
            }

        # 4. NORMAL / POWER SCALING
        multiplier = 5 
        if 'aarch64' in self.arch or 'arm' in self.arch: multiplier = 3 
        if "steam" in self.node or "deck" in self.node: multiplier = 3
             
        mem = psutil.virtual_memory()
        if mem.available < 2 * (1024**3): multiplier = 1
             
        ideal_pop = int(self.cpu_count * multiplier)
        
        if self.total_ram_gb > 32 and not battery: ideal_pop = self.cpu_count * 8 # Server
             
        ideal_pop = max(4, min(200, ideal_pop))
        
        # Restore Priority if we were gaming before
        try:
            if self.process.nice() > 0: self.process.nice(0)
        except: pass
        
        return {
            "population_size": ideal_pop,
            "throttle": 0.0,
            "parallel": True
        }
