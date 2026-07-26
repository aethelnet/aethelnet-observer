"""
Checkpoint Management Module

Handles checkpoint scanning, quality scoring, and pruning to prevent storage bloat.
"""

import os
import pickle
import glob
import json
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path


def load_metadata(checkpoint_path: str) -> Optional[Dict[str, Any]]:
    """Load verification metadata for a checkpoint."""
    try:
        metadata_path = checkpoint_path.replace('.pkl', '.metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def get_checkpoint_fitness(checkpoint_path: str) -> float:
    """
    Extract fitness score from checkpoint.
    Tries metadata first, then falls back to checkpoint data.
    """
    # Try metadata first (most reliable)
    metadata = load_metadata(checkpoint_path)
    if metadata:
        regime_perf = metadata.get('regime_performance', {})
        if regime_perf:
            # Use best regime fitness
            fitnesses = [m.get('fitness', 0.0) for m in regime_perf.values() if m.get('error') is None]
            if fitnesses:
                return max(fitnesses)
    
    # Fallback: try to load checkpoint and extract fitness
    # Note: Checkpoints don't store fitness directly, so this is a fallback
    try:
        with open(checkpoint_path, 'rb') as f:
            data = pickle.load(f)
            # Check if there's a fitness stored
            if 'fitness' in data:
                return data['fitness']
    except Exception:
        pass
    
    return 0.0


def get_checkpoint_score(checkpoint_path: str) -> float:
    """
    Calculate composite quality score for a checkpoint.
    Higher score = better checkpoint.
    
    Scoring:
    - Primary: Fitness score (from metadata or checkpoint)
    - Secondary: Universal score bonus (if verified and universal)
    - Tertiary: Verification status bonus (verified > unverified)
    - Age: Slight bonus for newer checkpoints (minimal impact)
    """
    score = 0.0
    
    # Primary: Fitness score
    fitness = get_checkpoint_fitness(checkpoint_path)
    score += fitness
    
    # Secondary: Universal score bonus (if verified)
    metadata = load_metadata(checkpoint_path)
    if metadata:
        if metadata.get('is_universal', False):
            universal_score = metadata.get('universal_score', 0.0)
            # Add bonus: universal_score * 100 (to make it meaningful)
            score += universal_score * 100
        
        # Tertiary: Verification bonus (small)
        if metadata.get('verified', False):
            score += 10.0  # Small bonus for verified checkpoints
    
    # Age bonus (minimal - newer is slightly better, but fitness is primary)
    try:
        file_age = os.path.getmtime(checkpoint_path)
        # Normalize age to 0-1 (newer = higher, but max bonus is only 1.0)
        import time
        current_time = time.time()
        age_days = (current_time - file_age) / (24 * 3600)
        # Bonus decreases with age, max 1.0 for very new files
        age_bonus = max(0, 1.0 - (age_days / 365.0))  # 1.0 for new, 0 for 1 year old
        score += age_bonus
    except Exception:
        pass
    
    return score


def scan_checkpoints() -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan all checkpoints and group by strategy type.
    
    Returns:
        Dict mapping strategy_name to list of checkpoint info dicts.
        Each checkpoint_info contains: path, fitness, universal_score, timestamp, metadata, score
    """
    checkpoints_by_strategy: Dict[str, List[Dict[str, Any]]] = {}
    
    # Scan all checkpoint directories
    checkpoint_dirs = [
        os.path.join(os.getcwd(), 'checkpoints', 'auto'),
        os.path.join(os.getcwd(), 'checkpoints'),
    ]
    
    for checkpoint_dir in checkpoint_dirs:
        if not os.path.exists(checkpoint_dir):
            continue
        
        # Find all .pkl files
        pattern = os.path.join(checkpoint_dir, '**', '*.pkl')
        checkpoint_files = glob.glob(pattern, recursive=True)
        
        for checkpoint_path in checkpoint_files:
            basename = os.path.basename(checkpoint_path).lower()
            
            # Detect strategy type from filename
            strategy_name = 'rat'  # default
            if 'tank' in basename:
                strategy_name = 'tank'
            elif 'turtle' in basename:
                strategy_name = 'turtle'
            elif 'alchemist' in basename:
                strategy_name = 'alchemist'
            elif 'architect' in basename:
                strategy_name = 'architect'
            
            # Get checkpoint info
            fitness = get_checkpoint_fitness(checkpoint_path)
            score = get_checkpoint_score(checkpoint_path)
            metadata = load_metadata(checkpoint_path)
            
            checkpoint_info = {
                'path': checkpoint_path,
                'filename': os.path.basename(checkpoint_path),
                'fitness': fitness,
                'score': score,
                'timestamp': os.path.getmtime(checkpoint_path),
                'metadata': metadata,
                'universal_score': metadata.get('universal_score', 0.0) if metadata else 0.0,
                'is_universal': metadata.get('is_universal', False) if metadata else False,
                'verified': metadata.get('verified', False) if metadata else False,
            }
            
            if strategy_name not in checkpoints_by_strategy:
                checkpoints_by_strategy[strategy_name] = []
            checkpoints_by_strategy[strategy_name].append(checkpoint_info)
    
    # Sort each strategy's checkpoints by score (descending)
    for strategy_name in checkpoints_by_strategy:
        checkpoints_by_strategy[strategy_name].sort(key=lambda x: x['score'], reverse=True)
    
    return checkpoints_by_strategy


def prune_checkpoints(
    max_per_strategy: int = 10,
    min_fitness_threshold: float = 0.0,
    keep_universal: bool = True,
    dry_run: bool = False,
    active_checkpoint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Prune checkpoints keeping only the best N per strategy.
    
    Args:
        max_per_strategy: Maximum checkpoints to keep per strategy
        min_fitness_threshold: Minimum fitness to keep (delete below this)
        keep_universal: Always keep universal strategies (even if over limit)
        dry_run: If True, only report what would be deleted
        active_checkpoint: Filename of currently active checkpoint (never delete)
    
    Returns:
        Dict with stats: deleted_count, kept_count, freed_space, etc.
    """
    checkpoints_by_strategy = scan_checkpoints()
    
    stats = {
        'deleted_count': 0,
        'kept_count': 0,
        'deleted_by_strategy': {},
        'kept_by_strategy': {},
        'freed_space': 0,
        'deleted_files': [],
        'kept_files': []
    }
    
    for strategy_name, checkpoints in checkpoints_by_strategy.items():
        if not checkpoints:
            continue
        
        # Separate universal and non-universal
        universal_checkpoints = [c for c in checkpoints if c.get('is_universal', False)]
        non_universal_checkpoints = [c for c in checkpoints if not c.get('is_universal', False)]
        
        # Always keep universal checkpoints if keep_universal=True
        to_keep = universal_checkpoints.copy() if keep_universal else []
        
        # Add top non-universal checkpoints
        remaining_slots = max_per_strategy - len(to_keep)
        if remaining_slots > 0:
            # Filter by min_fitness_threshold
            eligible = [c for c in non_universal_checkpoints if c['fitness'] >= min_fitness_threshold]
            to_keep.extend(eligible[:remaining_slots])
        
        # Also keep checkpoints that pass min_fitness_threshold even if not in top N
        # (but only if they're universal or we have room)
        for checkpoint in non_universal_checkpoints:
            if checkpoint in to_keep:
                continue
            if checkpoint['fitness'] >= min_fitness_threshold and len(to_keep) < max_per_strategy * 2:
                # Allow some flexibility for good checkpoints
                to_keep.append(checkpoint)
        
        # Safety: Never delete if it's the only checkpoint for a strategy
        if len(checkpoints) == 1:
            to_keep = checkpoints.copy()
        
        # Determine what to delete
        to_delete = [c for c in checkpoints if c not in to_keep]
        
        # Safety: Never delete active checkpoint
        if active_checkpoint:
            to_delete = [c for c in to_delete if c['filename'] != active_checkpoint]
            # If active was in to_delete, add it to to_keep
            for checkpoint in checkpoints:
                if checkpoint['filename'] == active_checkpoint and checkpoint not in to_keep:
                    to_keep.append(checkpoint)
        
        # Delete files
        deleted_count = 0
        freed_space = 0
        for checkpoint in to_delete:
            # Also delete metadata file if it exists
            metadata_path = checkpoint['path'].replace('.pkl', '.metadata.json')
            
            try:
                # Calculate file size before deletion
                if os.path.exists(checkpoint['path']):
                    freed_space += os.path.getsize(checkpoint['path'])
                    if not dry_run:
                        os.remove(checkpoint['path'])
                    deleted_count += 1
                    stats['deleted_files'].append(checkpoint['path'])
                
                if os.path.exists(metadata_path):
                    freed_space += os.path.getsize(metadata_path)
                    if not dry_run:
                        os.remove(metadata_path)
            except Exception as e:
                print(f"[CLEANUP] Error deleting {checkpoint['path']}: {e}")
        
        stats['deleted_count'] += deleted_count
        stats['kept_count'] += len(to_keep)
        stats['freed_space'] += freed_space
        stats['deleted_by_strategy'][strategy_name] = deleted_count
        stats['kept_by_strategy'][strategy_name] = len(to_keep)
        stats['kept_files'].extend([c['path'] for c in to_keep])
    
    return stats


def find_existing_checkpoints(strategy_name: str) -> List[Tuple[str, float]]:
    """
    Find all existing checkpoints for a strategy and return (path, fitness) tuples.
    Fitness is extracted from metadata if available, otherwise from checkpoint data.
    """
    checkpoints_by_strategy = scan_checkpoints()
    
    if strategy_name not in checkpoints_by_strategy:
        return []
    
    checkpoints = checkpoints_by_strategy[strategy_name]
    return [(c['path'], c['fitness']) for c in checkpoints]


def should_save_checkpoint(
    new_fitness: float,
    strategy_name: str,
    improvement_threshold: float = 0.05,
    always_save_first: bool = True
) -> Tuple[bool, Optional[str], str]:
    """
    Compare new checkpoint fitness with existing ones.
    
    Args:
        new_fitness: Fitness score of the new checkpoint
        strategy_name: Name of the strategy (e.g., 'rat', 'tank')
        improvement_threshold: Minimum improvement percentage required (default: 0.05 = 5%)
        always_save_first: Always save if no existing checkpoints
    
    Returns:
        Tuple of (should_save, best_existing_path, reason)
    """
    existing = find_existing_checkpoints(strategy_name)
    
    # Always save first checkpoint
    if not existing:
        if always_save_first:
            return True, None, "First checkpoint for this strategy"
        else:
            return True, None, "No existing checkpoints"
    
    # Find best existing checkpoint
    best_path, best_fitness = max(existing, key=lambda x: x[1])
    
    # Calculate improvement
    if best_fitness == 0:
        # If best is 0, any positive fitness is improvement
        improvement = float('inf') if new_fitness > 0 else 0.0
    else:
        improvement = (new_fitness - best_fitness) / abs(best_fitness)
    
    # Decision logic
    if improvement >= improvement_threshold:
        return True, best_path, f"New checkpoint is {improvement*100:.1f}% better than best existing (fitness: {new_fitness:.2f} vs {best_fitness:.2f})"
    else:
        return False, best_path, f"New checkpoint not significantly better ({improvement*100:.1f}% improvement, need {improvement_threshold*100:.1f}%). Best existing: {best_fitness:.2f}"



