#!/usr/bin/env python3
"""
Worker startup script for PixCrawler Celery workers.

This script starts Celery workers for different packages with
appropriate queue configurations.
"""

import argparse
import subprocess
import sys


def start_worker(package: str, queues: list, concurrency: int = 4):
    """
    Start a Celery worker for a specific package.

    Args:
        package: Package name (builder, validator, or all)
        queues: List of queues to consume
        concurrency: Number of worker processes
    """

    # Build the celery command
    cmd = [
        'celery',
        '-A', 'celery_core.app',
        'worker',
        '--loglevel=info',
        f'--concurrency={concurrency}',
        f'--queues={",".join(queues)}',
        f'--hostname={package}@%h'
    ]

    print(f"Starting {package} worker with queues: {queues}")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print(f"\nStopping {package} worker...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting {package} worker: {e}")
        sys.exit(1)

def start_flower(port: int = 5555):
    """Start Flower monitoring interface."""

    cmd = [
        'celery',
        '-A', 'celery_core.app',
        'flower',
        f'--port={port}'
    ]

    print(f"Starting Flower on port {port}")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print(f"\nStopping Flower...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Flower: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Start PixCrawler Celery workers')
    parser.add_argument(
        'worker_type',
        choices=['builder', 'validator', 'all', 'flower'],
        help='Type of worker to start'
    )
    parser.add_argument(
        '--concurrency', '-c',
        type=int,
        default=4,
        help='Number of worker processes (default: 4)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5555,
        help='Port for Flower (default: 5555)'
    )

    args = parser.parse_args()

    # Define queue configurations
    queue_configs = {
        'builder': [
            'builder.crawling',
            'builder.generation',
            'builder.processing'
        ],
        'validator': [
            'validator.validation',
            'validator.integrity',
            'validator.duplicates'
        ],
        'all': [
            'default',
            'builder.crawling',
            'builder.generation',
            'builder.processing',
            'validator.validation',
            'validator.integrity',
            'validator.duplicates'
        ]
    }

    if args.worker_type == 'flower':
        start_flower(args.port)
    else:
        queues = queue_configs[args.worker_type]
        start_worker(args.worker_type, queues, args.concurrency)

if __name__ == '__main__':
    main()
