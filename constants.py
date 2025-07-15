"""
This module defines constants and sets up the logging configuration for the PixCrawler application. It includes default file paths, supported search engines, image extensions, and ASCII art for the application banner. It also configures logging to a file and provides ANSI color codes for terminal output.

Classes:
    Colors: Provides ANSI escape codes for colored terminal output.

Features:
    - Defines core application constants such as default file paths and supported engines.
    - Configures file-based logging for the application.
    - Suppresses noisy warnings from external libraries.
    - Includes ASCII art for the application's visual branding.
    - Provides utility classes for colored console output.
"""

import logging
import warnings
from typing import Set, List, Literal, Final

__all__ = [
    'DEFAULT_CACHE_FILE',
    'DEFAULT_CONFIG_FILE',
    'DEFAULT_LOG_FILE',
    'ENGINES',
    'IMAGE_EXTENSIONS',
    'logger',
    'file_formatter'
]

# Default file paths for application data
DEFAULT_CACHE_FILE: str = "download_progress.json"
DEFAULT_CONFIG_FILE: str = "config.json"
DEFAULT_LOG_FILE: str = "pixcrawler.log"

# Supported search engines
ENGINES: Final[List[str]] = ["google", "bing", "baidu", "ddgs"]

# Image extensions supported by the application
IMAGE_EXTENSIONS: Final[Set[str]] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

# Suppress all warnings to prevent them from appearing in the console
warnings.filterwarnings("ignore")

# Configure logging to file only, no console output
logging.basicConfig(level=logging.CRITICAL)  # Set root logger to CRITICAL to suppress most messages

# Create our application logger
logger = logging.getLogger("pixcrawler")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger

# Create formatters
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create file handler
file_handler = logging.FileHandler(DEFAULT_LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Suppress urllib3 warnings specifically
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

# Silence other common noisy loggers
for logger_name in ["icrawler", "PIL", "downloader", "urllib3", "requests", "chardet", "charset_normalizer"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).propagate = False

# ASCII Art for Pixcrawler
PIXCRAWLER_ASCII: Final[str] = """
    ____  _       ______                    __           
   / __ \\(_)_  __/ ____/________ __      __/ /__  _____  
  / /_/ / /| |/_/ /   / ___/ __ `/ | /| / / / _ \\/ ___/  
 / ____/ / >  </ /___/ /  / /_/ /| |/ |/ / /  __/ /      
/_/   /_/_/_/|_|\\____/_/   \\__,_/ |__/|__/_/\\___/_/       
                                                        
"""


# ANSI Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


KEYWORD_MODE = Literal["auto", "disabled", "enabled"]
AI_MODELS = Literal["gpt4", "gpt4-mini"]
