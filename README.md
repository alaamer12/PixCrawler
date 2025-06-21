# PixCrawler 🕷️ - Configurable Image Dataset Builder

PixCrawler is a customizable image dataset builder that crawls the web using popular search engines like Google, Bing, and DuckDuckGo. It enables researchers, ML engineers, and developers to automate the collection of images for training datasets using a simple JSON-based configuration file.

## 📚 Features

* **JSON-driven configuration**
  * Define dataset name, categories, and keywords for search
* **Multi-engine support**
  * Uses Google, Bing, Baidu, and DuckDuckGo as fallback
* **Fast concurrent crawling**
  * Efficient image scraping using parallel downloads
* **Organized dataset structure**
  * Images are grouped by category and keyword
* **Duplicate detection**
  * Automatically removes duplicates using content and perceptual hashing
* **Progress tracking**
  * Continue from where you left off with progress caching
* **Keyword Generation**
  * Automatically generate effective keywords when none are provided
  * Optionally augment user-provided keywords with additional generated ones

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
  }
}
```

Then run:

```bash
python main.py -c config.json -m 20
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

## 🌟 Acknowledgements

* Google, Bing, and Baidu image search APIs
* DuckDuckGo search
* Python requests & icrawler

> Built with ❤️ by [Alaamer](https://github.com/alaamer12)
