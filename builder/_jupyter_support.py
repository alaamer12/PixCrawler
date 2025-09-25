"""Support functions for running PixCrawler in Jupyter/Colab environments.

This module provides utilities specifically designed to enhance the user experience
when PixCrawler is run within interactive notebook environments like Jupyter or Google Colab.
It includes functions for detecting the notebook environment and for colorizing output.

Functions:
    is_running_in_notebook: Checks if the current execution environment is a Jupyter notebook.
    print_help_colored: Prints formatted and colorized help text for argument parsers.
    colorize_output: Applies ANSI color styling to text output.

Features:
- Environment detection for Jupyter/Colab.
- Enhanced, colorized CLI output for better readability in notebooks.
- Utility for applying various color styles to text.
"""

import argparse

from builder._constants import Colors, PIXCRAWLER_ASCII


def is_running_in_notebook() -> bool:
    """
    Check if the code is running in a Jupyter notebook environment.

    Returns:
        bool: True if running in Jupyter notebook or Google Colab
    """
    try:
        import IPython  # type: ignore
        ipython = IPython.get_ipython()
        if ipython is not None and ('IPKernelApp' in ipython.config or 'google.colab' in str(ipython)):
            return True
        return False
    except ImportError:
        return False


def print_help_colored(parser: argparse.ArgumentParser) -> None:
    """
    Print help text with color highlighting.

    Args:
        parser: The argument parser
    """
    # Print the ASCII art
    print(f"{Colors.CYAN}{PIXCRAWLER_ASCII}{Colors.ENDC}")

    # Print description
    print(f"{Colors.BOLD}{Colors.GREEN}PixCrawler: Image Dataset Generator{Colors.ENDC}\n")

    # Get the help text
    help_text = parser.format_help()

    # Apply colors to different sections
    lines = help_text.split('\n')
    for line in lines:
        if line.startswith('usage:'):
            print(f"{Colors.YELLOW}{line}{Colors.ENDC}")
        elif line.endswith(':'):  # Group headers
            print(f"\n{Colors.BOLD}{Colors.BLUE}{line}{Colors.ENDC}")
        elif line.startswith('  -'):  # Arguments
            parts = line.split('  ', 2)
            if len(parts) >= 3:
                print(f"  {Colors.GREEN}{parts[1]}{Colors.ENDC}  {parts[2]}")
            else:
                print(line)
        else:
            print(line)

    print(f"\n{Colors.BOLD}For more information, visit: https://github.com/yourusername/pixcrawler{Colors.ENDC}\n")


def colorize_output(text: str, style: str = None) -> str:
    """
    Apply color styling to text output.

    Args:
        text: Text to colorize
        style: Style to apply (one of 'success', 'error', 'warning', 'info', 'bold')

    Returns:
        Colorized text
    """
    styles = {
        'success': f"{Colors.GREEN}{text}{Colors.ENDC}",
        'error': f"{Colors.RED}{text}{Colors.ENDC}",
        'warning': f"{Colors.YELLOW}{text}{Colors.ENDC}",
        'info': f"{Colors.CYAN}{text}{Colors.ENDC}",
        'bold': f"{Colors.BOLD}{text}{Colors.ENDC}",
    }
    return styles.get(style, text)
