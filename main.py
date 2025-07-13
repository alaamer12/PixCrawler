import argparse
import sys
from typing import Optional

from config import DatasetGenerationConfig
from constants import Colors, PIXCRAWLER_ASCII, DEFAULT_LOG_FILE
from constants import DEFAULT_CACHE_FILE, DEFAULT_CONFIG_FILE, KEYWORD_MODE, AI_MODELS
from generator import generate_dataset, update_logfile
from jupyter_support import is_running_in_notebook, print_help_colored


def parse_args_safely(parser: argparse.ArgumentParser) -> Optional[argparse.Namespace]:
    """
    Parse command line arguments safely, compatible with Jupyter environments.

    Returns:
        argparse.Namespace: Parsed arguments
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


def run_from_jupyter(config_path: str = DEFAULT_CONFIG_FILE,
                     max_images: int = 10,
                     output_dir: Optional[str] = None,
                     no_integrity: bool = False,
                     max_retries: int = 5,
                     continue_last: bool = False,
                     cache_file: str = DEFAULT_CACHE_FILE,
                     keyword_mode: KEYWORD_MODE = "auto",
                     ai_model: AI_MODELS = "gpt4-mini",
                     no_labels: bool = False) -> None:
    """
    Run PixCrawler directly from a Jupyter notebook or Google Colab.

    This function provides an easy way to use PixCrawler in notebook environments
    without dealing with command-line arguments.

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
    # Print ASCII art banner
    print(f"{Colors.CYAN}{PIXCRAWLER_ASCII}{Colors.ENDC}")
    print(f"{Colors.GREEN}PixCrawler: Image Dataset Generator{Colors.ENDC}")
    print(f"{Colors.YELLOW}Running in Jupyter/Colab mode{Colors.ENDC}\n")

    # Create configuration
    config = DatasetGenerationConfig(
        config_path=config_path,
        max_images=max_images,
        output_dir=output_dir,
        integrity=not no_integrity,
        max_retries=max_retries,
        continue_from_last=continue_last,
        cache_file=cache_file,
        keyword_generation=keyword_mode,
        ai_model=ai_model,
        generate_labels=not no_labels
    )

    # Show configuration
    print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
    print(f"  - Config file: {config_path}")
    print(f"  - Max images per keyword: {max_images}")
    print(f"  - Output directory: {output_dir or 'Auto (from config)'}")
    print(f"  - Image integrity checks: {not no_integrity}")
    print(f"  - Max retries: {max_retries}")
    print(f"  - Continue from last run: {continue_last}")
    print(f"  - Cache file: {cache_file}")
    print(f"  - Keyword generation mode: {keyword_mode}")
    print(f"  - AI model: {ai_model}")
    print(f"  - Generate labels: {not no_labels}\n")

    # Generate the dataset
    print(f"{Colors.BOLD}Starting dataset generation...{Colors.ENDC}")
    generate_dataset(config)

    # Print final message to indicate completion
    output_dir = config.output_dir or "dataset"
    print(f"\n{Colors.GREEN}✅ Dataset generation complete!{Colors.ENDC}")
    print(f"   - {Colors.BOLD}Output directory:{Colors.ENDC} {output_dir}")
    print(f"   - {Colors.BOLD}See the REPORT.md file in the output directory for detailed statistics{Colors.ENDC}")


def create_arg_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Create and configure argument parser with organized argument groups.

    Args:
        parser: The argument parser to configure

    Returns:
        Configured argument parser
    """
    # Add base configuration arguments
    _add_config_arguments(parser)

    # Add dataset generation control arguments
    _add_dataset_control_arguments(parser)

    # Add keyword generation options
    _add_keyword_generation_arguments(parser)

    # Add logging options
    _add_logging_arguments(parser)

    return parser


def _add_config_arguments(parser: argparse.ArgumentParser) -> None:
    """Add configuration file related arguments."""
    parser.add_argument(
        "-c", "--config",
        default=DEFAULT_CONFIG_FILE,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_FILE})"
    )
    parser.add_argument(
        "--cache",
        default=DEFAULT_CACHE_FILE,
        help=f"Cache file for progress tracking (default: {DEFAULT_CACHE_FILE})"
    )
    parser.add_argument(
        "--continue",
        dest="continue_last",
        action="store_true",
        help="Continue from last run using the progress cache"
    )


def _add_dataset_control_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments controlling dataset generation behavior."""
    parser.add_argument(
        "-m", "--max-images",
        type=int,
        default=10,
        help="Maximum number of images per keyword (default: 10)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Custom output directory (default: uses dataset_name from config)"
    )
    parser.add_argument(
        "--no-integrity",
        action="store_true",
        help="Skip image integrity checks (faster but may include corrupt images)"
    )
    parser.add_argument(
        "-r", "--max-retries",
        type=int,
        default=5,
        help="Maximum retry attempts for failed downloads (default: 5)"
    )
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Disable automatic label file generation"
    )


def _add_keyword_generation_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments related to keyword generation."""
    keyword_group = parser.add_argument_group('Keyword Generation')
    generation_mode = keyword_group.add_mutually_exclusive_group()
    generation_mode.add_argument(
        "--keywords-auto",
        action="store_const",
        const="auto",
        dest="keyword_mode",
        help="Generate keywords only if none provided (default)"
    )
    generation_mode.add_argument(
        "--keywords-enabled",
        action="store_const",
        const="enabled",
        dest="keyword_mode",
        help="Always generate additional keywords even when some are provided"
    )
    generation_mode.add_argument(
        "--keywords-disabled",
        action="store_const",
        const="disabled",
        dest="keyword_mode",
        help="Disable keyword generation completely"
    )
    parser.set_defaults(keyword_mode="auto")

    # AI model selection
    keyword_group.add_argument(
        "--ai-model",
        choices=["gpt4", "gpt4-mini"],
        default="gpt4-mini",
        help="AI model to use for keyword generation (default: gpt4-mini)"
    )


def _add_logging_arguments(parser: argparse.ArgumentParser) -> None:
    """Add logging configuration arguments."""
    log_group = parser.add_argument_group('Logging')
    log_group.add_argument(
        "--log-file",
        default=DEFAULT_LOG_FILE,
        help=f"Path to log file (default: {DEFAULT_LOG_FILE})"
    )


def main():
    """Main function to parse arguments and generate dataset"""
    # Print ASCII art banner
    print(f"{Colors.CYAN}{PIXCRAWLER_ASCII}{Colors.ENDC}")

    # Create the argument parser
    parser = argparse.ArgumentParser(description="PixCrawler: Image Dataset Generator", add_help=False)
    parser = create_arg_parser(parser)

    # Parse arguments safely (works in both scripts and notebooks)
    args = parse_args_safely(parser)

    # If help was requested, we've already printed it
    if args is None:
        if not is_running_in_notebook():
            sys.exit(0)
        return

    # Update log file if specified
    update_logfile(args.log_file)

    config = DatasetGenerationConfig(
        config_path=args.config,
        max_images=args.max_images,
        output_dir=args.output,
        integrity=not args.no_integrity,
        max_retries=args.max_retries,
        continue_from_last=args.continue_last,
        cache_file=args.cache,
        keyword_generation=args.keyword_mode,
        ai_model=args.ai_model,
        generate_labels=not args.no_labels
    )

    # Generate the dataset
    generate_dataset(config)

    # Print final message to indicate completion
    output_dir = config.output_dir or config.dataset_name
    print(f"\n{Colors.GREEN}✅ Dataset generation complete!{Colors.ENDC}")
    print(f"   - {Colors.BOLD}Output directory:{Colors.ENDC} {output_dir}")
    print(f"   - {Colors.BOLD}Log file:{Colors.ENDC} {args.log_file}")
    print(f"   - {Colors.BOLD}See the REPORT.md file in the output directory for detailed statistics{Colors.ENDC}")


if __name__ == "__main__":
    main()
