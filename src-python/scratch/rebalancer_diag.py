import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import get_settings

def main():
    settings = get_settings()
    print(f"--- SETTINGS DIAGNOSTICS ---")
    print(f"REBALANCER_DRY_RUN: {settings.REBALANCER_DRY_RUN} (Type: {type(settings.REBALANCER_DRY_RUN)})")
    print(f"EXECUTION_ENABLED: {settings.EXECUTION_ENABLED}")
    print(f"ENV_MODE: {settings.ENV_MODE}")
    print(f"TRADING_MODE: {settings.TRADING_MODE}")
    print(f"----------------------------")
    
    # Check if .env is being loaded
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    print(f"Checking for .env at: {env_path}")
    if os.path.exists(env_path):
        print("✅ .env file EXISTS.")
        with open(env_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "REBALANCER_DRY_RUN" in line:
                    print(f"Found in .env: {line.strip()}")
    else:
        print("❌ .env file NOT FOUND.")

if __name__ == "__main__":
    main()
