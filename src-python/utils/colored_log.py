"""
Colored Logging Utilities for Auratic Systems
Uses ANSI escape codes for terminal color output.
"""

# ANSI Color Codes
class Colors:
    # Reset
    RESET = "\033[0m"
    
    # Regular Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright/Bold Colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Background Colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    
    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"


# Pre-formatted log prefixes with colors
class LogPrefix:
    # Success/OK states - Green
    OK = f"{Colors.BRIGHT_GREEN}[OK]{Colors.RESET}"
    SUCCESS = f"{Colors.BRIGHT_GREEN}[SUCCESS]{Colors.RESET}"
    
    # Warnings - Yellow
    WARN = f"{Colors.BRIGHT_YELLOW}[WARN]{Colors.RESET}"
    CAUTION = f"{Colors.YELLOW}[CAUTION]{Colors.RESET}"
    
    # Errors/Critical - Red
    ERROR = f"{Colors.BRIGHT_RED}[ERROR]{Colors.RESET}"
    CRITICAL = f"{Colors.BG_RED}{Colors.WHITE}[CRITICAL]{Colors.RESET}"
    FAIL = f"{Colors.RED}[FAIL]{Colors.RESET}"
    
    # Info/Status - Cyan/Blue
    INFO = f"{Colors.CYAN}[INFO]{Colors.RESET}"
    STATUS = f"{Colors.BLUE}[STATUS]{Colors.RESET}"
    
    # System Components - Magenta
    BRAIN = f"{Colors.BRIGHT_MAGENTA}[BRAIN]{Colors.RESET}"
    BOT = f"{Colors.MAGENTA}[BOT]{Colors.RESET}"
    LIVE = f"{Colors.BRIGHT_MAGENTA}[LIVE]{Colors.RESET}"
    
    # Signals/Alerts - Bold Yellow/Red
    SIGNAL = f"{Colors.BOLD}{Colors.YELLOW}[SIGNAL]{Colors.RESET}"
    ALERT = f"{Colors.BOLD}{Colors.BRIGHT_RED}[ALERT]{Colors.RESET}"
    HOT = f"{Colors.BOLD}{Colors.RED}[HOT]{Colors.RESET}"
    
    # Data/Sync - Cyan
    SYNC = f"{Colors.CYAN}[SYNC]{Colors.RESET}"
    DATA = f"{Colors.BRIGHT_CYAN}[DATA]{Colors.RESET}"
    
    # Trading specific
    BUY = f"{Colors.BRIGHT_GREEN}[BUY]{Colors.RESET}"
    SELL = f"{Colors.BRIGHT_RED}[SELL]{Colors.RESET}"
    HOLD = f"{Colors.YELLOW}[HOLD]{Colors.RESET}"
    
    # States
    SLEEP = f"{Colors.DIM}[SLEEP]{Colors.RESET}"
    IDLE = f"{Colors.DIM}[IDLE]{Colors.RESET}"
    ACTIVE = f"{Colors.BRIGHT_GREEN}[ACTIVE]{Colors.RESET}"


def colorize(text: str, color: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{color}{text}{Colors.RESET}"


def gradient_text(text: str, start_color: str = Colors.CYAN, end_color: str = Colors.MAGENTA) -> str:
    """Simple two-color gradient effect (alternating characters)."""
    result = ""
    for i, char in enumerate(text):
        color = start_color if i % 2 == 0 else end_color
        result += f"{color}{char}"
    return result + Colors.RESET


# Convenience functions for common log patterns
def log_ok(msg: str) -> str:
    return f"{LogPrefix.OK} {msg}"

def log_warn(msg: str) -> str:
    return f"{LogPrefix.WARN} {msg}"

def log_error(msg: str) -> str:
    return f"{LogPrefix.ERROR} {msg}"

def log_signal(msg: str) -> str:
    return f"{LogPrefix.SIGNAL} {msg}"

def log_brain(msg: str) -> str:
    return f"{LogPrefix.BRAIN} {msg}"

def log_live(msg: str) -> str:
    return f"{LogPrefix.LIVE} {msg}"

def log_sync(msg: str) -> str:
    return f"{LogPrefix.SYNC} {msg}"


# Test function
if __name__ == "__main__":
    print(f"\n{LogPrefix.OK} System initialized successfully")
    print(f"{LogPrefix.WARN} Memory usage high (85%)")
    print(f"{LogPrefix.ERROR} Failed to connect to API")
    print(f"{LogPrefix.CRITICAL} Database connection lost!")
    print(f"{LogPrefix.BRAIN} Processing signal for BTCUSDT")
    print(f"{LogPrefix.SIGNAL} BUY detected (Z=-2.5)")
    print(f"{LogPrefix.LIVE} Executing trade...")
    print(f"{LogPrefix.BUY} +0.05 BTC @ $98,500")
    print(f"{LogPrefix.SELL} -0.05 BTC @ $99,200")
    print(f"\n{gradient_text('=== AURATIC SYSTEMS ONLINE ===')}\n")
