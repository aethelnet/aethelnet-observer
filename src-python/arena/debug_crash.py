import traceback
from arena.training_loop import run_battle

def main():
    print("--- DEBUGGING CRASH ---")
    config = {
        'decay': 0.741,
        'base_drag': 0.499,
        'base_spring': 0.0015,
        'action_threshold': 0.005
    }
    galaxy_config = {'contagion_factor': 1.0}
    
    try:
        # Run a short battle (Awakened)
        result = run_battle(0, config, 201, galaxy_config)
        print("Success:", result)
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()
