import sys
import os
import time

sys.path.append(os.getcwd())

print("P1. Importing setup_global_logging...")
from core.logger import setup_global_logging, get_logger
print("P2. setup_global_logging imported")

print("P3. Calling setup_global_logging...")
setup_global_logging()
print("P4. setup_global_logging called")

print("P5. Importing stream router...")
from routers import stream
print("P6. stream router imported")

print("P7. Importing trading_service...")
from services.trading_service import run_trading_service
print("P8. trading_service imported")

print("P9. Importing brain...")
from services.brain import get_engine
print("P10. brain imported")

print("P11. Success!")
