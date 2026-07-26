#!/usr/bin/env python3
"""
Helper script to simplify .env file by commenting out non-essential settings.
Only keeps API keys uncommented.
"""

import os
import re
from pathlib import Path

# Settings that should remain uncommented (API keys only)
KEEP_UNCOMMENTED = {
    'BINANCE_API_KEY',
    'BINANCE_SECRET_KEY',
    'BINANCE_TESTNET_API_KEY',
    'BINANCE_TESTNET_SECRET_KEY',
    'ALPACA_API_KEY',  # Optional, but if user has it, keep it
    'ALPACA_SECRET_KEY',  # Optional, but if user has it, keep it
}

# Settings that are critical and user might want to override
# These will be kept but with a comment explaining they can be uncommented
CRITICAL_OVERRIDES = {
    'BINANCE_TESTNET',
    'ENV_MODE',
    'EXECUTION_ENABLED',
    'ADMIN_TOKEN',  # Security critical
}

def simplify_env_file(env_path: str, backup: bool = True):
    """Simplify .env file by commenting out non-essential settings."""
    env_path = Path(env_path)
    
    if not env_path.exists():
        print(f"Error: {env_path} does not exist")
        return False
    
    # Read current .env
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Backup original
    if backup:
        backup_path = env_path.with_suffix('.env.backup')
        with open(backup_path, 'w') as f:
            f.writelines(lines)
        print(f"✅ Created backup: {backup_path}")
    
    # Process lines
    output_lines = []
    in_section = False
    current_section = None
    
    for line in lines:
        original_line = line
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            output_lines.append(original_line)
            continue
        
        # Check if it's a setting (KEY=VALUE format)
        if '=' in stripped and not stripped.startswith('#'):
            key = stripped.split('=', 1)[0].strip()
            
            # Keep API keys uncommented
            if key in KEEP_UNCOMMENTED:
                output_lines.append(original_line)
                continue
            
            # For critical overrides, add comment explaining
            if key in CRITICAL_OVERRIDES:
                output_lines.append(f"# {original_line.rstrip()}  # Uncomment to override default from settings.py\n")
                continue
            
            # Comment out everything else
            if not stripped.startswith('#'):
                output_lines.append(f"# {original_line.rstrip()}  # Uses default from settings.py\n")
            else:
                output_lines.append(original_line)
        else:
            output_lines.append(original_line)
    
    # Write simplified .env
    with open(env_path, 'w') as f:
        f.writelines(output_lines)
    
    print(f"✅ Simplified {env_path}")
    print(f"   - API keys remain uncommented")
    print(f"   - All other settings commented out")
    print(f"   - Defaults will be used from settings.py")
    
    return True

if __name__ == "__main__":
    import sys
    
    # Find .env file (project root)
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / ".env"
    
    if len(sys.argv) > 1:
        env_path = Path(sys.argv[1])
    
    if not env_path.exists():
        print(f"Error: {env_path} does not exist")
        print(f"Usage: python simplify_env.py [path/to/.env]")
        sys.exit(1)
    
    print(f"Simplifying {env_path}...")
    success = simplify_env_file(env_path, backup=True)
    
    if success:
        print("\n✅ Done! Your .env file now only has API keys uncommented.")
        print("   All other settings will use defaults from settings.py")
        print("   Uncomment settings in .env only if you need to override defaults")
    else:
        sys.exit(1)



