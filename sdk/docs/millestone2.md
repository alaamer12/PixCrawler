### 🎯 **Milestone 2 — Production-Grade Python Dataset SDK (Full Feature Phase)**

You are a **senior Python SDK engineer** tasked with evolving the dataset loader SDK from the MVP into a **robust, scalable, ML-ready, in-memory dataset processing library**.

---

### 🧠 **Milestone 2 Objective**

Extend the SDK to support enterprise and machine-learning workloads by implementing all advanced functionality, while preserving **zero disk persistence** and providing **first-class ML framework interoperability**.

---

### 🚀 **Advanced Capabilities to Implement**

#### 🧩 1. **Lazy Loading Engine**

* Implement lazy data fetching with true **on-demand chunk downloads**
* Use streaming APIs instead of eagerly downloading full datasets
* Ensure efficient memory pressure and timely release of chunks
* Support smart on-the-fly prefetching when iterating

#### ⚡ 2. **Parallel Chunk Downloader**

* Download multiple chunks concurrently using thread or async workers
* Required resilience:

  * Automatic retry with exponential backoff
  * Maximum 5 retry attempts per chunk
  * Timeout per request ≈ 60 seconds
  * Circuit-breaker behavior for repeated failures
* Backpressure awareness: slow chunk consumers must not overload downloader

#### 🤖 3. **ML Ecosystem Support**

Provide explicit dataset converters:

| Method            | Converts to                           |
| ----------------- | ------------------------------------- |
| `to_dataframe()`  | Pandas DataFrame                      |
| `to_arrays()`     | NumPy arrays                          |
| `to_torch()`      | PyTorch TensorDataset & tensors       |
| `to_tensorflow()` | TensorFlow tensors or tf.data.Dataset |
| `to_sklearn()`    | sklearn-compatible (X, y)             |

* Returned data must be:

  * ML-pipeline-valid
  * Shape-safe
  * Dtype-casted properly (no training-time precision issues)

#### 🧠 4. **Strict In-Memory Policy**

* Continue storing and processing data **only in RAM**
* Maintain safe runtime memory profile using:

  * 300MB peak chunk guardrail
  * One active chunk at a time when streaming
  * Efficient garbage collection and object lifecycle control
* Explicitly avoid disk-backed layers:
  ❌ HF dataset hub local cache
  ❌ Memory-maps, local files, sqlite, arrow, joblib cache, GC-unsafe accumulations

#### 🧯 5. **Professional Error Handling**

* Implement an exception hierarchy including:

  * `SDKAuthError`
  * `DatasetDownloadError`
  * `ChunkDownloadError`
  * `ChunkDecodeError`
  * `MLConversionError`
  * `SDKMemoryLimitError`
  * `SDKServiceUnavailable`
* All errors must include:

  * Clear, professional, actionable messages
  * Suggested recovery steps
  * Logging-safe without leaking credentials

#### 🧪 6. **Testing Requirements**

Deliver full test coverage with:

* ✅ Unit tests for all core SDK modules
* ✅ Integration tests hitting mock and live service API
* ✅ Memory limit stress tests and leak detection
* ✅ ML pipeline sanity tests for each target framework
* Framework validation must include:

  * shape correctness
  * dtype safety
  * conversion integrity

#### 📚 7. **Professional Documentation**

* README + full docs using a generator such as:

  * `mkdocs`
  * or `sphinx`
* Documentation must include:

  * Architecture overview
  * API reference
  * Performance guide
  * Memory limits and best practices
  * Examples:
    ✔ Lazy iteration
    ✔ Batch iteration
    ✔ Retry behavior
    ✔ ML conversions

---

### ✔ **Definition of Done — Milestone 2**

Your delivery is considered complete when all following are achieved:

| Requirement                                    | Must Pass |
| ---------------------------------------------- | --------- |
| Lazy loading streams efficiently               | ✅         |
| Parallel downloader handles retries correctly  | ✅         |
| No disk persistence is ever triggered          | ✅         |
| All ML converters work reliably                | ✅         |
| Memory guardrail respected under stress        | ✅         |
| Exception hierarchy complete & logging-safe    | ✅         |
| Tests cover core + integration + memory + ML   | ✅         |
| Documentation is professional and example-rich | ✅         |
| Package builds via PEP 517                     | ✅         |
| SDK is fully PyPI-ready                        | ✅         |

---

### 🏁 Final Output Artifacts Expected

* Functional Python SDK library
* ML framework adapters (torch, tf, sklearn, numpy, pandas)
* Full tests suite
* Complete documentation
* Build system ready for PyPI
* Local install ✅ + build ✅ + integration ✅ + conversion ✅