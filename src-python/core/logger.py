import logging
import sys
import os
from datetime import datetime
from typing import Optional

# ANSI Colors for console output
class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"

class AuraticFormatter(logging.Formatter):
    """
    Standard formatter for Auratic Systems.
    Enforces:
    - ISO 8601 Timestamps
    - Strict Level Names (INFO, WARN, ERROR, DEBUG)
    - No Emojis in system logs
    """

    FORMAT_STR = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.MAGENTA + Colors.BOLD,
    }

    def format(self, record):
        # Apply color if output stream supports it
        log_fmt = self.FORMAT_STR
        if sys.stderr.isatty():
             color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
             # We color the levelname and the message slightly? Or just the prefix?
             # Let's clean it up: [TIME] [LEVEL] [NAME] MSG
             # We will color the [LEVEL] part.
             
             record.levelname = f"{color}{record.levelname}{Colors.RESET}"
             record.name = f"{Colors.BLUE}{record.name}{Colors.RESET}"

        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%dT%H:%M:%S")
        return formatter.format(record)

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Factory to get a standardized logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # dedicated handler to avoid duplicates if get_logger is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(AuraticFormatter())
        logger.addHandler(handler)
        
    # Allow propagation to root logger to ensure logs reach the file handler
    logger.propagate = True

    return logger

def setup_global_logging(level: int = logging.INFO):
    """
    Configures the root logger to use the Auratic standard.
    Useful for valid overrides of third-party logs if needed.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Also log to file if possible
    try:
        from logging.handlers import RotatingFileHandler
        # Log to the centralized logs directory
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "log")
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))
        handlers.append(file_handler)
    except Exception:
        pass

    for h in handlers:
        root_logger.addHandler(h)

    # --- SOVEREIGN LOGGING (Superset Integration) ---
    # try:
    #     from core.sovereign_logger import add_sovereign_handler
    #     # Path relative to project root (2 levels up from backend/core)
    #     project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    #     db_path = os.path.join(project_root, "market_data.db")
    #     add_sovereign_handler(logger_name="", db_path=db_path) # Empty name = root logger
    # except Exception as e:
    #     print(f"⚠️ Sovereign Logging failed to initialize: {e}")

    # --- Noise Suppression (Legacy "Zero Noise" Policy) ---
    noisy_modules = [
        "ccxt",
        "urllib3",
        "asyncio",
        "aiohttp",
        "uvicorn.access",
        "uvicorn.error",
        "websockets",
        "multipart",
        "watchfiles",
        "bleak",
        "dbus_fast",
        "dbus_next"
    ]
    
    for module in noisy_modules:
        logging.getLogger(module).setLevel(logging.WARNING)
        
    # Hyper-suppress CCXT base exchange to avoid scanning noise
    logging.getLogger("ccxt.base.exchange").setLevel(logging.CRITICAL)

def shutdown_logging():
    """
    Flushes and closes all logging handlers.
    Called on system shutdown.
    """
    logging.shutdown()
