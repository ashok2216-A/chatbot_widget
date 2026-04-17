import logging
import sys

# Standard ANSI escape sequences for text colors
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"

class LightningFireFormatter(logging.Formatter):
    """Custom formatting injecting emojis and colors depending on the log severity."""
    
    FORMATS = {
        logging.DEBUG: f"{CYAN}[DEBUG]{RESET} %(asctime)s - %(name)s - %(message)s",
        logging.INFO: f"{GREEN}[INFO]{RESET} %(asctime)s - %(name)s - %(message)s",
        logging.WARNING: f"{YELLOW}[WARNING]{RESET} %(asctime)s - %(name)s - %(message)s",
        logging.ERROR: f"{RED}[ERROR]{RESET} %(asctime)s - %(name)s - %(message)s",
        logging.CRITICAL: f"{BOLD}{RED}[CRITICAL]{RESET} %(asctime)s - %(name)s - %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def get_logger(name: str):
    """Returns a pre-configured colorful logger instance."""
    logger = logging.getLogger(name)
    
    # Avoid duplicating logs if get_logger is called multiple times for the same name
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(LightningFireFormatter())
        
        logger.addHandler(console_handler)
        # Prevent log messages from propagating up to the root logger natively
        logger.propagate = False
        
    return logger
