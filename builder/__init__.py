"""
PixCrawler Builder Package

A comprehensive image dataset builder that crawls the web using popular search engines.

This package provides a unified Builder class that encapsulates all functionality
for generating image datasets with AI-powered keyword generation, multi-engine
downloading, integrity checking, and comprehensive reporting.

Classes:
    Builder: Main class providing unified interface for dataset generation

Example:
    ```python
    from builder import Builder

    # Simple usage
    builder = Builder("config.json")
    builder.generate()

    # Advanced usage
    builder = Builder(
        config_path="config.json",
        max_images=50,
        output_dir="./my_dataset",
        integrity=True,
        generate_labels=True
    )
    builder.set_ai_model("gpt4")
    builder.enable_keyword_generation()
    builder.generate()
    ```
"""

from builder._builder import Builder

__version__ = "0.1.0"
__author__ = "PixCrawler Team"
__email__ = "team@pixcrawler.com"

__all__ = ['Builder']
