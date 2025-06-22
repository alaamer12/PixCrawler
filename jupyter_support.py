"""
Support functions for running PixCrawler in Jupyter/Colab environments.
"""

import argparse
from typing import Optional

from constants import Colors, PIXCRAWLER_ASCII

def is_running_in_notebook() -> bool:
    """
    Check if the code is running in a Jupyter notebook environment.
    
    Returns:
        bool: True if running in Jupyter notebook or Google Colab
    """
    try:
        import IPython # type: ignore
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

def parse_args_safely(parser: argparse.ArgumentParser) -> Optional[argparse.Namespace]:
    """
    Parse command line arguments safely, compatible with Jupyter environments.
    
    Args:
        parser: The argument parser to use
        
    Returns:
        argparse.Namespace: Parsed arguments or None if help was requested
    """
    # Add help argument manually
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')
    
    # First handle the case where we're in a notebook
    if is_running_in_notebook():
        # In Jupyter/Colab, only use sys.argv[0] (script name) and ignore other arguments
        # that might be automatically passed by the notebook environment
        args, unknown = parser.parse_known_args([])
        
        # If they want help, print it specially formatted
        if args.help:
            print_help_colored(parser)
            return None
            
        return args
    
    # In normal terminal environment, parse as usual
    args, unknown = parser.parse_known_args()
    
    # If they want help, print it specially formatted and exit
    if args.help:
        print_help_colored(parser)
        return None
        
    # Warning about unknown arguments
    if unknown:
        print(f"{Colors.YELLOW}Warning: Unknown arguments: {unknown}{Colors.ENDC}")
        
    return args

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