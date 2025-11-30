# Reusing Your Dataset Database with PixCrawler SDK

**Version:** 1.0
**Status:** Guide

---

## Overview

PixCrawler serves as more than just a scraping tool; it acts as a centralized, versioned repository for your image datasets. The PixCrawler Python SDK enables you to reuse this "remote database" of images across multiple environments, projects, and pipelines without the need for manual file management or massive local storage.

This guide demonstrates how to leverage the SDK to integrate PixCrawler datasets into your existing data infrastructure.

## Getting Started via UI

After creating a dataset, you can access the **Usage Guide** directly from the dashboard:

1.  Navigate to your dataset dashboard.
2.  Click the **Usage Guide** button in the top header.
3.  This page provides:
    -   The exact `pip install` command.
    -   A ready-to-copy Python snippet pre-filled with your `job_id`.
    -   Direct navigation back to the dashboard.

## Core Patterns

### 1. The "Streaming Source" Pattern

Instead of downloading a dataset once and managing files on disk, treat PixCrawler as a streaming source. This allows you to:
- Run training jobs on ephemeral cloud instances without pre-loading data.
- Share datasets across teams without duplicating storage.

### 2. The "ETL" Pattern (Extract, Transform, Load)

Use the SDK as the "Extract" step in your ETL pipeline to populate other databases, such as:
- **Vector Databases** for similarity search.
- **SQL Databases** for metadata querying.
- **Data Lakes** (S3, GCS) for archival.

---

## Integration Examples

### 1. Populating a Vector Database (e.g., ChromaDB)

This example shows how to stream images from PixCrawler, compute embeddings, and store them in a vector database for semantic search.

```python
import chromadb
from pixcrawler import load_dataset
from PIL import Image
import numpy as np
# Assume you have an embedding function
from my_model import compute_embedding 

# 1. Connect to Vector DB
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="my_dataset_embeddings")

# 2. Load PixCrawler Dataset (Lazy Stream)
dataset = load_dataset(job_id="job_abc123", api_key="your_api_key")

# 3. Stream, Embed, and Index
batch_size = 64
for images, labels in dataset.iter_batches(batch_size=batch_size):
    # images is (B, H, W, C) numpy array
    
    # Compute embeddings (pseudo-code)
    embeddings = compute_embedding(images) 
    
    # Prepare IDs and Metadata
    ids = [f"img_{i}" for i in range(len(images))]
    metadatas = [{"label": label} for label in labels]
    
    # Add to ChromaDB
    collection.add(
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

print("Indexing complete!")
```

### 2. Syncing to a Local SQL Database (SQLite/PostgreSQL)

Store dataset metadata and local file references in a SQL database for complex querying.

```python
import sqlite3
import os
from pixcrawler import load_dataset
from PIL import Image

# 1. Setup Database
conn = sqlite3.connect('datasets.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS images
             (id INTEGER PRIMARY KEY, job_id TEXT, label TEXT, file_path TEXT)''')

# 2. Load Dataset
job_id = "job_xyz789"
dataset = load_dataset(job_id=job_id, api_key="your_api_key")

# 3. Save Files Locally and Record in DB
save_dir = f"./data/{job_id}"
os.makedirs(save_dir, exist_ok=True)

count = 0
for image, label in dataset:
    # Convert numpy to PIL and save
    img = Image.fromarray(image)
    filename = f"{count}.jpg"
    file_path = os.path.join(save_dir, filename)
    img.save(file_path)
    
    # Insert into DB
    c.execute("INSERT INTO images (job_id, label, file_path) VALUES (?, ?, ?)",
              (job_id, str(label), file_path))
    count += 1

conn.commit()
conn.close()
print(f"Imported {count} images to SQL database.")
```

### 3. Continuous Model Retraining

Set up a script that checks for new datasets and triggers retraining.

```python
from pixcrawler import PixCrawlerClient, load_dataset
from my_ml_pipeline import train_model

client = PixCrawlerClient(api_key="your_api_key")

def check_and_train(project_id):
    # Get latest completed job for project
    jobs = client.list_jobs(project_id=project_id, status="completed")
    if not jobs:
        return
        
    latest_job = jobs[0]
    
    # Check if we've already trained on this job (pseudo-code)
    if is_new_job(latest_job.id):
        print(f"Found new dataset: {latest_job.id}. Starting training...")
        
        # Stream data directly into training
        dataset = load_dataset(latest_job.id, api_key="your_api_key")
        train_model(dataset)
        
        mark_job_as_processed(latest_job.id)

# Run periodically...
```

---

## Best Practices for Reuse

1.  **Cache Locally When Possible**: If you plan to iterate over the same dataset multiple times (e.g., multiple training epochs), consider using `dataset.to_arrays()` (if memory permits) or saving to a local fast SSD format (like TFRecords or WebDataset) during the first pass.
2.  **Use Tags**: Tag your PixCrawler jobs (e.g., "v1.0", "production", "staging") to easily identify which datasets to pull into your downstream applications.
3.  **Monitor Usage**: Streaming large datasets repeatedly can consume bandwidth. For frequent access, a one-time download to a local cache or a cloud bucket in the same region is recommended.
