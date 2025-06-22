import logging


DEFAULT_CACHE_FILE = "download_progress.json"
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_LOG_FILE = "pixcrawler.log"
ENGINES = ["google", "bing", "baidu", "ddgs"]

# Image extensions supported
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

# Configure logging to file and console
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create file handler for detailed logs
file_handler = logging.FileHandler(DEFAULT_LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create console handler for minimal output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)