import os

def get_project_root():
    """Get the project root directory"""
    return os.environ.get('AURATIC_PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_master_key_path():
    """Get the full path to master.key file"""
    return os.path.join(get_project_root(), 'backend', 'master.key')

def get_handshake_key_path():
    """Get the full path to handshake.key file"""
    return os.path.join(get_project_root(), 'handshake.key')

# Monkey patch common master.key paths to use the correct location
def patch_master_key_paths():
    """Patch any hardcoded master.key paths in the system"""
    import sys
    import builtins
    
    # Store original open function
    original_open = builtins.open
    
    def patched_open(file, *args, **kwargs):
        # If someone tries to open 'backend/master.key', redirect to correct path
        if isinstance(file, str) and file == 'backend/master.key':
            file = get_master_key_path()
        return original_open(file, *args, **kwargs)
    
    # Replace built-in open function
    builtins.open = patched_open

# Apply the patch when this module is imported
patch_master_key_paths()
