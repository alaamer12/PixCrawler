# PixCrawler Python SDK Specification

**Version:** 1.0  
**Last Updated:** 2025-10-30  
**Status:** Architecture Specification

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [API Reference](#api-reference)
6. [Usage Examples](#usage-examples)
7. [Integration with ML Frameworks](#integration-with-ml-frameworks)
8. [CLI Tool](#cli-tool)
9. [Architecture](#architecture)
10. [Performance & Memory](#performance--memory)
11. [Error Handling](#error-handling)
12. [Best Practices](#best-practices)

---

## Overview

### Purpose

The PixCrawler Python SDK provides a simple, memory-efficient way to download and use image datasets created with PixCrawler. It follows the design patterns of popular ML dataset libraries like `kaggle-hub` and `huggingface datasets`.

### Key Features

✅ **Lazy Loading** - Downloads chunks on-demand, not all at once  
✅ **Memory Efficient** - Streams data without disk caching  
✅ **ML Framework Ready** - Works with scikit-learn, PyTorch, TensorFlow  
✅ **Parallel Downloads** - Multi-threaded chunk downloading  
✅ **Progress Tracking** - Real-time download progress  
✅ **Type Safe** - Full type hints for IDE support  

### Design Philosophy

- **"Good enough to start, flexible enough to improve"**
- In-memory assembly (no disk cache required)
- Lazy loading (download only what you need)
- Standard ML workflow compatibility

---

## Installation

### Via pip

```bash
pip install pixcrawler-sdk
```

### From source

```bash
git clone https://github.com/pixcrawler/pixcrawler-sdk.git
cd pixcrawler-sdk
pip install -e .
```

### Requirements

- Python 3.10+
- httpx (async HTTP client)
- pandas (optional, for DataFrame support)
- torch (optional, for PyTorch support)
- tensorflow (optional, for TensorFlow support)

---

## Quick Start

### Basic Usage

```python
from pixcrawler import load_dataset

# Load dataset (lazy loading)
dataset = load_dataset(
    job_id="job_abc123",
    api_key="your_api_key"
)

# Iterate through images
for image, label in dataset:
    print(f"Image shape: {image.shape}, Label: {label}")

# Or use with scikit-learn
X, y = dataset.to_arrays()
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y)
```

### With PyTorch

```python
from pixcrawler import load_dataset
from torch.utils.data import DataLoader

dataset = load_dataset("job_abc123", api_key="your_key")
torch_dataset = dataset.to_torch()

dataloader = DataLoader(
    torch_dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4
)

for batch in dataloader:
    images, labels = batch
    # Train your model
```

---

## Core Concepts

### 1. Lazy Loading

The SDK does **not** download all data upfront. Instead:

- Downloads chunks only when accessed
- Keeps current chunk in memory
- Releases memory after processing
- Minimizes memory footprint

```python
dataset = load_dataset("job_id")  # No download yet

# Download happens here
for image, label in dataset:  # Downloads chunk 1
    process(image)
    # After chunk 1 exhausted, downloads chunk 2
```

### 2. Streaming API

Process data without loading everything into memory:

```python
# Memory-efficient iteration
for image, label in dataset:
    train_model(image, label)

# Batch streaming
for batch in dataset.iter_batches(batch_size=64):
    images, labels = batch
    train_model(images, labels)
```

### 3. Chunk Management

- Datasets are stored as compressed chunks (500 images each)
- SDK downloads chunks in parallel when possible
- Automatically manages chunk lifecycle (download → use → release)

---

## API Reference

### `load_dataset()`

Load a PixCrawler dataset.

```python
def load_dataset(
    job_id: str,
    api_key: str,
    base_url: str = "https://api.pixcrawler.com",
    max_workers: int = 4,
    timeout: int = 300,
    verify_ssl: bool = True
) -> Dataset:
    """
    Load a PixCrawler dataset with lazy loading.
    
    Args:
        job_id: Job/dataset identifier
        api_key: PixCrawler API key
        base_url: API base URL (default: production)
        max_workers: Number of parallel download threads
        timeout: Download timeout in seconds
        verify_ssl: Verify SSL certificates
    
    Returns:
        Dataset object for iteration and conversion
    
    Raises:
        AuthenticationError: Invalid API key
        NotFoundError: Job not found
        JobNotCompleteError: Job still processing
    
    Example:
        >>> dataset = load_dataset("job_123", api_key="key")
        >>> for image, label in dataset:
        ...     print(image.shape)
    """
```

### `Dataset` Class

Main dataset class for iteration and conversion.

#### Methods

##### `__iter__()`

```python
def __iter__(self) -> Iterator[tuple[np.ndarray, Any]]:
    """
    Iterate through dataset one image at a time.
    
    Yields:
        Tuple of (image, label) where:
        - image: numpy array (H, W, C)
        - label: label data (str, int, dict, etc.)
    
    Example:
        >>> for image, label in dataset:
        ...     process(image, label)
    """
```

##### `iter_batches()`

```python
def iter_batches(
    self,
    batch_size: int = 32,
    drop_last: bool = False
) -> Iterator[tuple[np.ndarray, list]]:
    """
    Iterate through dataset in batches.
    
    Args:
        batch_size: Number of images per batch
        drop_last: Drop last incomplete batch
    
    Yields:
        Tuple of (images, labels) where:
        - images: numpy array (B, H, W, C)
        - labels: list of labels
    
    Example:
        >>> for images, labels in dataset.iter_batches(batch_size=64):
        ...     train_model(images, labels)
    """
```

##### `to_arrays()`

```python
def to_arrays(self) -> tuple[np.ndarray, np.ndarray]:
    """
    Load entire dataset into numpy arrays.
    
    Warning: Loads all data into memory. Use only for small datasets.
    
    Returns:
        Tuple of (X, y) where:
        - X: images array (N, H, W, C)
        - y: labels array (N,)
    
    Example:
        >>> X, y = dataset.to_arrays()
        >>> X_train, X_test, y_train, y_test = train_test_split(X, y)
    """
```

##### `to_dataframe()`

```python
def to_dataframe(self) -> pd.DataFrame:
    """
    Convert dataset to pandas DataFrame.
    
    Returns:
        DataFrame with columns:
        - image: numpy array
        - label: label data
        - metadata: dict of additional info
    
    Example:
        >>> df = dataset.to_dataframe()
        >>> df.head()
    """
```

##### `to_torch()`

```python
def to_torch(
    self,
    transform: Optional[Callable] = None
) -> torch.utils.data.Dataset:
    """
    Convert to PyTorch Dataset.
    
    Args:
        transform: Optional transform function
    
    Returns:
        PyTorch Dataset object
    
    Example:
        >>> from torchvision import transforms
        >>> transform = transforms.Compose([
        ...     transforms.ToTensor(),
        ...     transforms.Normalize(mean=[0.5], std=[0.5])
        ... ])
        >>> torch_dataset = dataset.to_torch(transform=transform)
        >>> dataloader = DataLoader(torch_dataset, batch_size=32)
    """
```

##### `to_tensorflow()`

```python
def to_tensorflow(self) -> tf.data.Dataset:
    """
    Convert to TensorFlow Dataset.
    
    Returns:
        TensorFlow Dataset object
    
    Example:
        >>> tf_dataset = dataset.to_tensorflow()
        >>> tf_dataset = tf_dataset.batch(32).prefetch(1)
        >>> model.fit(tf_dataset, epochs=10)
    """
```

##### Properties

```python
@property
def info(self) -> DatasetInfo:
    """Get dataset metadata and statistics."""

@property
def num_images(self) -> int:
    """Total number of images in dataset."""

@property
def num_chunks(self) -> int:
    """Total number of chunks."""

@property
def chunk_size(self) -> int:
    """Images per chunk (typically 500)."""
```

---

## Usage Examples

### Example 1: Simple Iteration

```python
from pixcrawler import load_dataset

dataset = load_dataset("job_123", api_key="key")

# Process images one by one
for image, label in dataset:
    print(f"Image: {image.shape}, Label: {label}")
```

### Example 2: Batch Processing

```python
from pixcrawler import load_dataset

dataset = load_dataset("job_123", api_key="key")

# Process in batches
for images, labels in dataset.iter_batches(batch_size=64):
    # images shape: (64, H, W, C)
    # labels: list of 64 labels
    process_batch(images, labels)
```

### Example 3: scikit-learn Integration

```python
from pixcrawler import load_dataset
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load dataset
dataset = load_dataset("job_123", api_key="key")
X, y = dataset.to_arrays()

# Flatten images for sklearn
X_flat = X.reshape(X.shape[0], -1)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X_flat, y, test_size=0.2, random_state=42
)

# Train model
clf = RandomForestClassifier()
clf.fit(X_train, y_train)
print(f"Accuracy: {clf.score(X_test, y_test)}")
```

### Example 4: PyTorch Training Loop

```python
from pixcrawler import load_dataset
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim

# Load dataset
dataset = load_dataset("job_123", api_key="key")
torch_dataset = dataset.to_torch()

# Create dataloader
train_loader = DataLoader(
    torch_dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4
)

# Training loop
model = MyModel()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters())

for epoch in range(10):
    for images, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
```

### Example 5: TensorFlow Training

```python
from pixcrawler import load_dataset
import tensorflow as tf

# Load dataset
dataset = load_dataset("job_123", api_key="key")
tf_dataset = dataset.to_tensorflow()

# Prepare dataset
tf_dataset = tf_dataset.batch(32).prefetch(tf.data.AUTOTUNE)

# Build and train model
model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(32, 3, activation='relu'),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(10, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.fit(tf_dataset, epochs=10)
```

### Example 6: Pandas DataFrame Analysis

```python
from pixcrawler import load_dataset

dataset = load_dataset("job_123", api_key="key")
df = dataset.to_dataframe()

# Analyze dataset
print(df.head())
print(df['label'].value_counts())
print(df.describe())

# Filter by label
cat_images = df[df['label'] == 'cat']
print(f"Found {len(cat_images)} cat images")
```

---

## Integration with ML Frameworks

### scikit-learn

```python
from pixcrawler import load_dataset
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

dataset = load_dataset("job_123", api_key="key")
X, y = dataset.to_arrays()

# Flatten and normalize
X_flat = X.reshape(X.shape[0], -1)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_flat)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2
)

# Grid search
param_grid = {'C': [0.1, 1, 10], 'kernel': ['rbf', 'linear']}
grid = GridSearchCV(SVC(), param_grid, cv=5)
grid.fit(X_train, y_train)

print(f"Best params: {grid.best_params_}")
print(f"Test accuracy: {grid.score(X_test, y_test)}")
```

### PyTorch

```python
from pixcrawler import load_dataset
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
import torch.nn as nn

# Custom transform
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                       std=[0.229, 0.224, 0.225])
])

dataset = load_dataset("job_123", api_key="key")
torch_dataset = dataset.to_torch(transform=transform)

# Train/val split
train_size = int(0.8 * len(torch_dataset))
val_size = len(torch_dataset) - train_size
train_dataset, val_dataset = random_split(
    torch_dataset, [train_size, val_size]
)

# Dataloaders
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32)

# Training
model = MyModel()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters())

for epoch in range(10):
    model.train()
    for images, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    
    # Validation
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for images, labels in val_loader:
            outputs = model(images)
            val_loss += criterion(outputs, labels).item()
    
    print(f"Epoch {epoch}: Val Loss = {val_loss/len(val_loader)}")
```

### TensorFlow/Keras

```python
from pixcrawler import load_dataset
import tensorflow as tf
from tensorflow.keras import layers, models

dataset = load_dataset("job_123", api_key="key")
tf_dataset = dataset.to_tensorflow()

# Preprocessing
def preprocess(image, label):
    image = tf.image.resize(image, [224, 224])
    image = tf.cast(image, tf.float32) / 255.0
    return image, label

tf_dataset = tf_dataset.map(preprocess)

# Train/val split
dataset_size = dataset.num_images
train_size = int(0.8 * dataset_size)
train_dataset = tf_dataset.take(train_size).batch(32).prefetch(1)
val_dataset = tf_dataset.skip(train_size).batch(32).prefetch(1)

# Model
model = models.Sequential([
    layers.Conv2D(32, 3, activation='relu', input_shape=(224, 224, 3)),
    layers.MaxPooling2D(),
    layers.Conv2D(64, 3, activation='relu'),
    layers.MaxPooling2D(),
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(10, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# Train
history = model.fit(
    train_dataset,
    validation_data=val_dataset,
    epochs=10
)
```

---

## CLI Tool

### Installation

CLI tool is included with the SDK:

```bash
pip install pixcrawler-sdk
```

### Commands

#### Download Dataset

```bash
pixcrawler download <job_id> --api-key <key> [options]
```

**Options:**
- `--output-dir`: Output directory (default: `./datasets`)
- `--format`: Output format: `numpy`, `images`, `zip` (default: `numpy`)
- `--max-workers`: Parallel download threads (default: 4)
- `--no-progress`: Disable progress bar

**Examples:**

```bash
# Download to numpy arrays
pixcrawler download job_123 --api-key mykey

# Download as image files
pixcrawler download job_123 --api-key mykey --format images --output-dir ./my_dataset

# Fast parallel download
pixcrawler download job_123 --api-key mykey --max-workers 8
```

#### List Datasets

```bash
pixcrawler list --api-key <key>
```

#### Dataset Info

```bash
pixcrawler info <job_id> --api-key <key>
```

**Output:**
```
Dataset: job_123
Status: completed
Images: 10,000
Chunks: 20
Size: 2.5 GB
Created: 2025-10-30 12:00:00
Labels: cat, dog, bird (3 classes)
```

---

## Architecture

### Package Structure

```
pixcrawler-sdk/
├── pixcrawler/
│   ├── __init__.py
│   ├── client.py          # API client
│   ├── dataset.py         # Dataset class
│   ├── downloader.py      # Chunk downloader
│   ├── loaders.py         # ML framework loaders
│   ├── exceptions.py      # Custom exceptions
│   └── cli.py             # CLI tool
├── tests/
│   ├── test_dataset.py
│   ├── test_downloader.py
│   └── test_loaders.py
├── pyproject.toml
└── README.md
```

### Data Flow

```
User Code
    ↓
load_dataset(job_id, api_key)
    ↓
API Client: GET /api/v1/jobs/{job_id}
    ↓
Get chunk metadata (URLs, count, size)
    ↓
Dataset object created (lazy)
    ↓
User iterates: for image, label in dataset
    ↓
Downloader: Download chunk_001.zip (parallel)
    ↓
Extract chunk in memory
    ↓
Yield images one by one
    ↓
Chunk exhausted → Download chunk_002.zip
    ↓
Repeat until all chunks processed
```

### Memory Management

**Chunk Lifecycle:**
1. **Download**: Fetch compressed chunk from blob storage
2. **Decompress**: Extract in memory (no disk write)
3. **Yield**: Serve images to user code
4. **Release**: Clear memory when chunk exhausted
5. **Repeat**: Download next chunk

**Memory Usage:**
- Active chunk: ~250 MB (500 images × 500 KB avg)
- Decompression buffer: ~50 MB
- Total per chunk: ~300 MB
- Peak memory: ~600 MB (2 chunks during transition)

---

## Performance & Memory

### Memory Efficiency

**Lazy Loading:**
```python
# Only loads one chunk at a time (~300 MB)
for image, label in dataset:
    process(image)
```

**Eager Loading:**
```python
# Loads entire dataset into memory
X, y = dataset.to_arrays()  # May use 10+ GB for large datasets
```

### Download Performance

**Parallel Downloads:**
- Default: 4 parallel threads
- Configurable: `max_workers` parameter
- Typical speed: 50-100 MB/s (depends on network)

**Chunk Size:**
- 500 images per chunk
- ~250 MB compressed
- ~500 MB uncompressed

### Benchmarks

**Small Dataset (5,000 images, 10 chunks):**
- Download time: 30-60 seconds
- Memory usage: ~300 MB (peak)
- Iteration time: 2-3 minutes

**Large Dataset (100,000 images, 200 chunks):**
- Download time: 10-20 minutes (parallel)
- Memory usage: ~300 MB (peak, lazy loading)
- Iteration time: 30-40 minutes

---

## Error Handling

### Exception Hierarchy

```python
PixCrawlerError (base)
├── AuthenticationError      # Invalid API key
├── NotFoundError           # Job not found
├── JobNotCompleteError     # Job still processing
├── DownloadError           # Chunk download failed
├── DecompressionError      # Chunk extraction failed
└── NetworkError            # Network/timeout issues
```

### Example

```python
from pixcrawler import load_dataset
from pixcrawler.exceptions import (
    AuthenticationError,
    JobNotCompleteError,
    DownloadError
)

try:
    dataset = load_dataset("job_123", api_key="key")
    
    for image, label in dataset:
        process(image)
        
except AuthenticationError:
    print("Invalid API key")
except JobNotCompleteError as e:
    print(f"Job still processing: {e.progress}% complete")
except DownloadError as e:
    print(f"Download failed: {e.chunk_id}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

**Automatic Retries:**
- Network errors: 3 retries with exponential backoff
- Chunk download failures: 3 retries
- Decompression errors: No retry (fail fast)

**Manual Retry:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def load_with_retry(job_id, api_key):
    return load_dataset(job_id, api_key)

dataset = load_with_retry("job_123", "key")
```

---

## Best Practices

### 1. Use Lazy Loading for Large Datasets

```python
# ✅ Good: Memory efficient
for image, label in dataset:
    train_model(image, label)

# ❌ Bad: Loads everything into memory
X, y = dataset.to_arrays()  # May crash with large datasets
```

### 2. Batch Processing

```python
# ✅ Good: Efficient batch processing
for images, labels in dataset.iter_batches(batch_size=64):
    train_model(images, labels)

# ❌ Bad: Processing one by one is slow
for image, label in dataset:
    train_model(image.reshape(1, -1), [label])
```

### 3. Parallel Downloads

```python
# ✅ Good: Fast parallel downloads
dataset = load_dataset("job_id", api_key="key", max_workers=8)

# ❌ Bad: Slow sequential downloads
dataset = load_dataset("job_id", api_key="key", max_workers=1)
```

### 4. Error Handling

```python
# ✅ Good: Handle specific errors
try:
    dataset = load_dataset("job_id", api_key="key")
except JobNotCompleteError as e:
    print(f"Wait for job to complete: {e.progress}%")
except AuthenticationError:
    print("Check your API key")

# ❌ Bad: Catch-all exception
try:
    dataset = load_dataset("job_id", api_key="key")
except Exception:
    pass  # What went wrong?
```

### 5. Progress Tracking

```python
# ✅ Good: Show progress to user
from tqdm import tqdm

dataset = load_dataset("job_id", api_key="key")
for image, label in tqdm(dataset, total=dataset.num_images):
    process(image)

# ❌ Bad: No feedback
for image, label in dataset:
    process(image)  # User has no idea how long this takes
```

### 6. Resource Cleanup

```python
# ✅ Good: Use context manager (future feature)
with load_dataset("job_id", api_key="key") as dataset:
    for image, label in dataset:
        process(image)
# Automatic cleanup

# ✅ Also good: Explicit cleanup
dataset = load_dataset("job_id", api_key="key")
try:
    for image, label in dataset:
        process(image)
finally:
    dataset.close()  # Release resources
```

---

## Roadmap

### Version 1.0 (MVP)
- ✅ Lazy loading
- ✅ Streaming API
- ✅ scikit-learn support
- ✅ PyTorch support
- ✅ TensorFlow support
- ✅ CLI tool
- ✅ Parallel downloads

### Version 1.1
- [ ] Disk caching (optional)
- [ ] Resume interrupted downloads
- [ ] Dataset versioning
- [ ] Custom transforms pipeline

### Version 2.0
- [ ] Distributed loading (multi-node)
- [ ] Smart prefetching
- [ ] Compression options
- [ ] Dataset merging

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

**Document Owner:** SDK Team  
**Review Cycle:** Quarterly  
**Next Review:** 2025-01-30
