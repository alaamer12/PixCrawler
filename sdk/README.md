# PixCrawler SDK

A Python SDK for loading and transforming datasets efficiently for Machine Learning applications.

## Installation

```bash
pip install -e .
```

## Usage

### Authentication

Set your API key in the environment variables:

```bash
export SERVICE_API_KEY="your_api_key"
```

### Loading a Dataset

```python
from pixcrawler import load_dataset

# Load dataset (downloads into memory)
dataset = load_dataset("dataset-id-123")

# Iterate over items
for item in dataset:
    print(item)
```
