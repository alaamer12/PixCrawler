#!/usr/bin/env python3
"""
Platform-aware Celery worker startup script.

This script automatically detects the platform and starts the Celery worker
with the appropriate pool configuration:
- Windows: Uses 'solo' pool (prefork doesn't work well on Windows)
- Linux/Unix: Uses 'prefork' pool (best performance for CPU-bound tasks)
- macOS: Uses 'prefork' pool (Unix-based, supports prefork)

Usage:
    python start_celery_worker.py [--concurrency N] [--loglevel LEVEL]
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

from celery_core.config import get_celery_settings
from utility.logging_config import get_logger

logger = get_logger(__name__)

def get_platform_info():
    """Get platform information for worker configuration."""
    system = platform.system()
    machine = platform.machine()
    python_version = platform.python_version()
    
    return {
        'system': system,
        'machine': machine,
        'python_version': python_version,
        'platform_string': f"{system}-{machine}"
    }

def get_worker_command(concurrency=None, loglevel='info', queues=None):
    """
    Build the Celery worker command with platform-appropriate settings.
    
    Args:
        concurrency: Number of worker processes (None for auto-detect)
        loglevel: Logging level
        queues: Comma-separated queue names (None for all queues)
    
    Returns:
        List of command arguments
    """
    settings = get_celery_settings()
    platform_info = get_platform_info()
    
    # Get platform-appropriate pool
    worker_pool = settings.get_worker_pool()
    
    # Adjust concurrency based on platform and pool
    if concurrency is None:
        if worker_pool == 'solo':
            concurrency = 1  # Solo pool is single-threaded
        else:
            concurrency = settings.worker_concurrency
    
    # Build command
    cmd = [
        sys.executable, '-m', 'celery',
        '-A', 'celery_core.app',
        'worker',
        f'--pool={worker_pool}',
        f'--concurrency={concurrency}',
        f'--loglevel={loglevel}',
    ]
    
    # Add queues if specified
    if queues:
        cmd.extend([f'--queues={queues}'])
    else:
        # Default to all queues
        cmd.extend(['--queues=crawl,validation,maintenance,default'])
    
    # Platform-specific optimizations
    if platform_info['system'] == 'Windows':
        # Windows-specific settings
        cmd.extend([
            '--without-gossip',  # Reduce overhead
            '--without-mingle',  # Reduce startup time
        ])
    elif platform_info['system'] == 'Linux':
        # Linux-specific optimizations
        cmd.extend([
            '--optimization=fair',  # Better task distribution
        ])
    
    return cmd

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Start Celery worker with platform-appropriate configuration'
    )
    parser.add_argument(
        '--concurrency', '-c',
        type=int,
        help='Number of worker processes (auto-detected if not specified)'
    )
    parser.add_argument(
        '--loglevel', '-l',
        default='info',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Logging level (default: info)'
    )
    parser.add_argument(
        '--queues', '-Q',
        help='Comma-separated queue names (default: all queues)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print command without executing'
    )
    
    args = parser.parse_args()
    
    # Get platform info
    platform_info = get_platform_info()
    settings = get_celery_settings()
    
    print("🚀 PixCrawler Celery Worker Startup")
    print("=" * 50)
    print(f"Platform: {platform_info['system']} ({platform_info['machine']})")
    print(f"Python: {platform_info['python_version']}")
    print(f"Worker Pool: {settings.get_worker_pool()}")
    print(f"Broker: {settings.broker_url}")
    print(f"Result Backend: {settings.result_backend}")
    print()
    
    # Build command
    cmd = get_worker_command(
        concurrency=args.concurrency,
        loglevel=args.loglevel,
        queues=args.queues
    )
    
    print("Command:")
    print(" ".join(cmd))
    print()
    
    if args.dry_run:
        print("🔍 Dry run mode - command not executed")
        return
    
    # Import tasks to ensure they're registered
    print("📦 Importing task modules...")
    try:
        import builder.tasks
        import celery_core.tasks
        import validator.tasks
        print("✅ All task modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import task modules: {e}")
        sys.exit(1)
    
    print()
    print("🎯 Starting Celery worker...")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        # Start the worker
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Worker stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Worker failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()