import os
import glob
import importlib.util
import inspect
import logging

logger = logging.getLogger("StrategyLoader")

class StrategyLoader:
    """
    The Librarian.
    Unlocks the Dark Archives by scanning and loading strategies dynamically.
    """
    
    def __init__(self, base_path: str = None):
        if base_path:
             self.base_path = base_path
        else:
             # Default to current file's directory -> strategies
             # backend/arena/loader.py -> backend/arena/strategies
             self.base_path = os.path.join(os.path.dirname(__file__), "strategies")
             
    def discover_strategies(self) -> dict:
        """
        Recursively finds all valid strategy classes in subdirectories.
        Returns: { 'strategy_name': StrategyInstance, ... }
        """
        import sys
        archives = {}
        
        # We want to scan specific subfolders: personal, phd, science
        # But also just recursively everything to be safe/thorough
        search_path = os.path.join(self.base_path, "**", "*.py")
        files = glob.glob(search_path, recursive=True)
        
        logger.info(f"[Loader] Scanning {len(files)} files in Dark Archives...")
        
        for filepath in files:
            # Skip __init__, tests, or excluded
            if "__init__" in filepath or "test_" in filepath:
                continue
                
            try:
                # MULTIPROCESSING FIX: Use full dotted module path
                # instead of just the basename. This allows pickle to
                # resolve the module in worker subprocesses.
                short_name = os.path.splitext(os.path.basename(filepath))[0]
                
                # Compute full dotted path from filesystem
                abs_path = os.path.abspath(filepath)
                parts = abs_path.replace(os.sep, '/').split('/')
                try:
                    backend_idx = parts.index('backend')
                    module_name = '.'.join(parts[backend_idx:]).replace('.py', '')
                except ValueError:
                    module_name = short_name  # Fallback
                
                # KEY FIX: If this module was already imported by Python's
                # standard import system, reuse it. DO NOT create a duplicate.
                # Creating a duplicate breaks pickle's identity check in
                # multiprocessing workers.
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                else:
                    spec = importlib.util.spec_from_file_location(module_name, filepath)
                    if not (spec and spec.loader):
                        continue
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                # Inspect for Classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Filter criteria:
                    # 1. Has 'on_tick' method (Duck Typing)
                    # 2. Is defined in this module (not imported)
                    if hasattr(obj, 'on_tick') and obj.__module__ == module_name:
                         # Instantiate
                         try:
                             instance = obj()
                             key = short_name.lower()
                             
                             if key in archives:
                                 key = f"{key}_{name.lower()}"
                                 
                             archives[key] = instance
                         except Exception as e:
                             logger.warning(f"  ! Failed to instantiate {name} in {module_name}: {e}")
                                 
            except Exception as e:
                # logger.warning(f"  ! Failed to load module {filepath}: {e}")
                pass
                
                
        logger.info(f"[Loader] Unlocked {len(archives)} Strategies from the Dark Archives.")
        return archives

    def discover_gamemodes(self) -> list:
        """
        Scans for GameMode scenarios in backend/arena/gamemodes/
        """
        import sys
        modes = []
        # Path to gamemodes relative to where loader is? 
        # backend/arena/loader.py -> backend/arena/gamemodes
        gm_path = os.path.join(os.path.dirname(__file__), "gamemodes", "**", "*.py")
        files = glob.glob(gm_path, recursive=True)
        
        logger.info(f"[Loader] Scanning {len(files)} gamemodes...")
        
        for filepath in files:
            if "__init__" in filepath: continue
            
            try:
                # MULTIPROCESSING FIX: Use full dotted module path
                short_name = os.path.splitext(os.path.basename(filepath))[0]
                abs_path = os.path.abspath(filepath)
                parts = abs_path.replace(os.sep, '/').split('/')
                try:
                    backend_idx = parts.index('backend')
                    module_name = '.'.join(parts[backend_idx:]).replace('.py', '')
                except ValueError:
                    module_name = short_name
                
                # Reuse existing module if already imported
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                else:
                    spec = importlib.util.spec_from_file_location(module_name, filepath)
                    if not (spec and spec.loader):
                        continue
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Duck Typing: Check for 'generate_scenario'
                    if hasattr(obj, 'generate_scenario') and obj.__module__ == module_name:
                         modes.append(obj)
            except:
                pass
                
        logger.info(f"[Loader] Unlocked {len(modes)} Gamemodes.")
        return modes
