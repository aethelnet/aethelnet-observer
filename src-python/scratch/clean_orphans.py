
import os
import signal
import subprocess

my_pid = os.getpid()
print(f"My PID: {my_pid}")

# Get all python processes related to the project
try:
    output = subprocess.check_output(["pgrep", "-f", "auratic-systems-prime"]).decode().split()
    pids = [int(p) for p in output]
    
    for pid in pids:
        if pid == my_pid:
            continue
        try:
            # Check if it's still running
            os.kill(pid, 0)
            print(f"Killing orphaned process: {pid}")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
except subprocess.CalledProcessError:
    print("No matching processes found.")
