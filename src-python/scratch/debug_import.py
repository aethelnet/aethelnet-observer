import sys
import os

# The script is in backend/scratch/
# Project root is two levels up from that
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

print(f"Project Root: {project_root}")
print(f"Sys Path: {sys.path[:3]}")

try:
    from services.execution import get_execution_engine
    print(f"SUCCESS: Imported get_execution_engine from {get_execution_engine.__module__}")
    import inspect
    print(f"Defined in: {inspect.getfile(get_execution_engine)}")
except ImportError as e:
    print(f"FAILED: {e}")
    # Try to see what's in services.execution
    try:
        import services.execution as execution
        print(f"Module execution found at: {execution.__file__}")
        print(f"Attributes: {[attr for attr in dir(execution) if 'engine' in attr.lower()]}")
    except Exception as e2:
        print(f"Could not even import module: {e2}")
