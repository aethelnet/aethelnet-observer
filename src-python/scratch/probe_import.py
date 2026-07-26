import sys
import os
print("1. sys and os imported")
import time
print("2. time imported")

# Add the project root to Python path
sys.path.append(os.getcwd())
print(f"3. Path added: {os.getcwd()}")

print("4. Attempting to import main...")
try:
    import main
    print("5. main imported successfully")
except Exception as e:
    print(f"6. FAILED: {e}")
