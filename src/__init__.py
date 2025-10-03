"""
PixCrawler Shared Components Package

This package contains shared components and utilities that are used across
multiple packages in the PixCrawler ecosystem.

Classes:
    ReportGenerator: Comprehensive report generation for dataset operations

Features:
    - Markdown report generation with tables and sections
    - Keyword generation tracking and reporting
    - Download statistics and error reporting
    - Detailed timestamp and duration tracking
"""

from src.report_generator import ReportGenerator

__version__ = "0.1.0"
__author__ = "PixCrawler Team"
__email__ = "team@pixcrawler.com"

__all__ = ["ReportGenerator"]