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

print("P7. Importing data router...")
from routers import data
print("P8. data router imported")

print("P9. Importing settings...")
from config.settings import get_settings
print("P10. settings imported")

print("P11. Importing brain...")
from services.brain import get_engine
print("P12. brain imported")

print("P13. Success!")
