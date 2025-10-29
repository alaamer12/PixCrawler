#!/usr/bin/env python3
"""
Script to run storage tests with various configurations.

This script provides a convenient way to run storage tests with different
options, generate reports, and validate test coverage.

Usage:
    python run_storage_tests.py                    # Run all storage tests
    python run_storage_tests.py --unit             # Run only unit tests
    python run_storage_tests.py --integration      # Run only integration tests
    python run_storage_tests.py --coverage         # Run with coverage report
    python run_storage_tests.py --fast             # Skip slow tests
    python run_storage_tests.py --verbose          # Verbose output
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code.
    
    Args:
        cmd: Command to run as list of strings
        description: Description of what the command does
        
    Returns:
        Exit code from the command
    """
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run PixCrawler storage tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Run all storage tests
  %(prog)s --unit                   Run only unit tests
  %(prog)s --integration            Run only integration tests
  %(prog)s --coverage               Generate coverage report
  %(prog)s --fast                   Skip slow tests
  %(prog)s --verbose                Show detailed output
  %(prog)s --unit --coverage        Run unit tests with coverage
  %(prog)s --smoke                  Run quick smoke tests
        """
    )
    
    # Test selection options
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run only smoke tests (quick validation)"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    
    # Output options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output"
    )
    
    # Coverage options
    parser.add_argument(
        "--coverage",
        "-c",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    # Report options
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--xml",
        action="store_true",
        help="Generate XML coverage report (for CI/CD)"
    )
    
    # Debugging options
    parser.add_argument(
        "--pdb",
        action="store_true",
        help="Drop into debugger on failures"
    )
    parser.add_argument(
        "--lf",
        "--last-failed",
        action="store_true",
        help="Run only tests that failed last time"
    )
    parser.add_argument(
        "--ff",
        "--failed-first",
        action="store_true",
        help="Run failed tests first, then others"
    )
    
    # Performance options
    parser.add_argument(
        "--durations",
        type=int,
        metavar="N",
        help="Show N slowest test durations"
    )
    
    # Parallel execution
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        metavar="N",
        help="Run tests in parallel with N workers (requires pytest-xdist)"
    )
    
    # Custom test path
    parser.add_argument(
        "test_path",
        nargs="?",
        help="Specific test file or directory to run"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["pytest"]
    
    # Determine test files to run
    if args.test_path:
        test_files = [args.test_path]
    elif args.unit:
        test_files = ["tests/test_storage_unit.py"]
    elif args.integration:
        test_files = ["tests/test_storage_integration.py"]
    else:
        test_files = ["tests/test_storage_unit.py", "tests/test_storage_integration.py"]
    
    cmd.extend(test_files)
    
    # Add markers
    markers = []
    if args.smoke:
        markers.append("smoke")
    if args.fast:
        markers.append("not slow")
    
    if markers:
        cmd.extend(["-m", " and ".join(markers)])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    elif args.quiet:
        cmd.append("-q")
    else:
        cmd.append("-v")
    
    # Add coverage options
    if args.coverage or (not args.no_coverage and not args.quiet):
        cmd.extend([
            "--cov=backend.storage",
            "--cov-report=term-missing"
        ])
        
        if args.html:
            cmd.append("--cov-report=html")
        
        if args.xml:
            cmd.append("--cov-report=xml")
    
    # Add debugging options
    if args.pdb:
        cmd.append("--pdb")
    
    if args.lf:
        cmd.append("--lf")
    
    if args.ff:
        cmd.append("--ff")
    
    # Add performance options
    if args.durations:
        cmd.extend(["--durations", str(args.durations)])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add standard options
    cmd.extend([
        "--strict-markers",
        "--tb=short"  # Shorter traceback format
    ])
    
    # Run tests
    exit_code = run_command(cmd, "Storage Tests")
    
    # Print summary
    print(f"\n{'='*80}")
    if exit_code == 0:
        print("✅ All tests passed!")
        if args.coverage or not args.no_coverage:
            print("\n📊 Coverage report generated:")
            if args.html:
                print("   HTML: htmlcov/storage/index.html")
            if args.xml:
                print("   XML: coverage_storage.xml")
            print("   Terminal: See above")
    else:
        print("❌ Some tests failed!")
        print(f"   Exit code: {exit_code}")
    print(f"{'='*80}\n")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
