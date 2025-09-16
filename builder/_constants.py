"""
This module defines constants for the PixCrawler application and provides centralized logging.
It includes default file paths, supported search engines, image extensions, and ASCII art 
for the application banner. Uses the centralized logging_config package for consistent logging.

Classes:
    Colors: Provides ANSI escape codes for colored terminal output.

Features:
    - Defines core application constants such as default file paths and supported engines.
    - Uses centralized logging configuration from logging_config package.
    - Includes ASCII art for the application's visual branding.
    - Provides utility classes for colored console output.
"""

import warnings
from typing import Set, List, Literal, Final

# Import centralized logging
from logging_config import get_logger

__all__ = [
    'DEFAULT_CACHE_FILE',
    'DEFAULT_CONFIG_FILE',
    'DEFAULT_LOG_FILE',
    'ENGINES',
    'IMAGE_EXTENSIONS',
    'logger'
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

# Get logger from centralized logging system
logger = get_logger("builder")

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
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


KEYWORD_MODE = Literal["auto", "disabled", "enabled"]
AI_MODELS = Literal["gpt4", "gpt4-mini"]
