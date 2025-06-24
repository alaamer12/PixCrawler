#!/usr/bin/env python3
"""
PixCrawler for Google Colab

This script provides an easy interface for running PixCrawler in Google Colab
or other Jupyter notebook environments.

Usage in Colab:
    # Install dependencies
    !pip install g4f duckduckgo_search icrawler
    
    # Copy files to Colab
    !git clone https://github.com/yourusername/pixcrawler.git
    %cd pixcrawler
    
    # Import and run
    from colab_run import run_pixcrawler
    
    run_pixcrawler(
        config_path="config.json",  # Path to your configuration file
        max_images=10,              # Max images per keyword
        output_dir=None,            # Custom output directory (optional)
    )
"""

from main import run_from_jupyter as _run_from_jupyter
from jupyter_support import Colors, PIXCRAWLER_ASCII


# noinspection PyIncorrectDocstring
def run_pixcrawler(**kwargs):
    """
    Run PixCrawler with the specified parameters.
    
    Args:
        config_path: Path to configuration file (default: config.json)
        max_images: Maximum images per keyword (default: 10)
        output_dir: Custom output directory (default: derived from config)
        no_integrity: Skip image integrity checks (default: False)
        max_retries: Maximum retry attempts (default: 5)
        continue_last: Continue from last run (default: False)
        cache_file: Path to cache file (default: download_progress.json)
        keyword_mode: Keyword generation mode (auto, enabled, disabled) (default: auto)
        ai_model: AI model for keyword generation (gpt4, gpt4-mini) (default: gpt4-mini)
        no_labels: Disable automatic label generation (default: False)
    """
    _run_from_jupyter(**kwargs)


if __name__ == "__main__":
    # If run as a script, show usage information
    print(f"{Colors.CYAN}{PIXCRAWLER_ASCII}{Colors.ENDC}")
    print(f"{Colors.GREEN}PixCrawler for Google Colab{Colors.ENDC}")
    print(f"\n{Colors.YELLOW}This script is designed to be imported in Google Colab, not run directly.{Colors.ENDC}")
    print(f"\n{Colors.BOLD}Usage example:{Colors.ENDC}")
    print("""
    # Install dependencies
    !pip install g4f duckduckgo_search icrawler
    
    # Import and run
    from colab_run import run_pixcrawler
    
    run_pixcrawler(
        config_path="config.json",  # Path to your configuration file
        max_images=10,              # Max images per keyword
        output_dir=None,            # Custom output directory (optional)
    )
    """)
