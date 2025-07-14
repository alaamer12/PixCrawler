# PixCrawler 🕷️ - Configurable Image Dataset Builder

PixCrawler is a customizable image dataset builder that crawls the web using popular search engines like Google, Bing, and DuckDuckGo. It enables researchers, ML engineers, and developers to automate the collection of images for training datasets using a simple JSON-based configuration file.

## 📚 Features

* **JSON-driven Configuration**: Define dataset name, categories, and keywords for search.
* **Multi-Engine Support**: Utilizes Google, Bing, Baidu, and DuckDuckGo for comprehensive image crawling.
* **Fast Concurrent Crawling**: Efficient image scraping through parallel downloads.
* **Organized Dataset Structure**: Images are automatically grouped by category and keyword for easy management.
* **Duplicate Detection**: Employs content and perceptual hashing to automatically remove duplicate images.
* **Progress Tracking**: Features progress caching, allowing you to resume interrupted downloads seamlessly.
* **AI-Powered Keyword Generation**:
  * Automatically generates effective keywords when none are provided.
  * Optionally augments user-provided keywords with additional AI-generated terms for broader searches.
* **Automated Label Generation**:
  * Creates corresponding label files for each image.
  * Supports multiple formats: TXT, JSON, CSV, and YAML.
  * Maintains a hierarchical structure that mirrors the image dataset for machine learning readiness.
* **Image Integrity Checks**: Verifies the validity and integrity of downloaded images.
* **Comprehensive Reporting**: Generates detailed reports on the dataset generation process, including download statistics, duplicate findings, and integrity check results.

## 🔧 Usage

Create a config file following the example in `config.json.example`:

```json
{
  "dataset_name": "animals",
  "categories": {
    "mammals": [
      "dog",
      "cat",
      "elephant"
    ],
    "birds": [
      "eagle",
      "penguin",
      "parrot"
    ]
  },
  "options": {
    "max_images": 20,
    "generate_keywords": true
  }
}
```

Then run:

```bash
python generator.py
```

Or with custom options:

```bash
python generator.py -c my_config.json -m 30 --generate-keywords
```

### Configuration Options

You can specify options either in the config file or via command-line arguments. Command-line arguments take precedence over config file options.

**Config File Options:**

```json
"options": {
  "max_images": 20,
  "output_dir": "datasets/my_dataset",
  "integrity": true,
  "max_retries": 3,
  "cache_file": "my_progress.json",
  "generate_keywords": true,
  "disable_keyword_generation": false
}
```

This will create a dataset with the following structure:

```
animals/
├── mammals/
│   ├── dog/
│   │   ├── 001.jpg
│   │   ├── 002.jpg
│   │   └── ...
│   ├── cat/
│   └── elephant/
└── birds/
    ├── eagle/
    ├── penguin/
    └── parrot/
```

## 🚀 Command Line Arguments

```
python main.py --help
```

- `-c, --config`: Path to configuration file (required)
- `-m, --max-images`: Maximum number of images per keyword (default: 10)
- `-o, --output`: Custom output directory (default: uses dataset_name from config)
- `--no-integrity`: Skip integrity checks
- `-r, --max-retries`: Maximum retry attempts (default: 5)
- `--continue`: Continue from last run
- `--cache`: Cache file for progress tracking (default: download_progress.json)
- `--generate-keywords`: Generate additional keywords for categories (even when user-provided)
- `--no-generate-keywords`: Disable automatic keyword generation
- `--no-labels`: Disable automatic label file generation

## 🌟 Acknowledgements

* Google, Bing, and Baidu image search APIs
* DuckDuckGo search
* Python requests & icrawler

> Built with ❤️ by [Alaamer](https://github.com/alaamer12)
