### 🎯 **Milestone 1 — Minimum Viable Python SDK (MVP Phase)**

You are a **senior Python SDK engineer** tasked with delivering the **MVP version** of a dataset loader SDK that works end-to-end with our service **with no additional features beyond the integration and download flow**.

---

### 🧠 **Milestone 1 Objective**

Deliver a **minimal, stable, locally installable Python SDK** that:

1. Connects to our internal dataset service API
2. Authenticates successfully using service-provided credentials
3. Downloads the requested dataset
4. Assembles it entirely **in-memory (NO disk cache, NO temp files, NO database, NO local storage)**
5. Provides a **Dataset class** that can iterate over data after download
6. Exposes a single entrypoint: **`load_dataset()`**
7. Supports dataset downloading **in a scalable, stream-safe manner** without exceeding memory limits

---

### 🧩 **Required Functional Scope**

#### ✅ **Service Integration**

* The SDK must communicate with our **internal dataset service** via HTTP API
* Requests should support:

  * API authentication header (e.g., `Authorization: Bearer <token>` or equivalent)
  * Optional custom headers provided by service
  * Secure requests (TLS assumed but not SDK responsibility)

#### 🔐 **Authentication**

* Implement authentication using credentials supplied by our service:

  * API Key or access token or both
  * Credentials may come from:

    * Environment variables (`SERVICE_API_KEY`, `SERVICE_API_TOKEN`)
    * Or configuration object passed into `load_dataset()`
* SDK must fail fast on invalid/missing credentials

#### 📥 **Dataset Download**

* The SDK must:

  * Download dataset files or dataset JSON/CSV responses from service
  * Validate response status codes properly
  * Ensure **no corruption, no partial success states**
  * Support **automatic retries (3 attempts)** on connection failures or 5xx responses
  * Timeout requests that exceed **60 seconds**
  * Download request must be **synchronous (blocking)** just during MVP

#### 🧠 **In-Memory Assembly**

* The dataset must be stored:

  * In RAM only
  * With a **safe peak memory guardrail of ~300MB**
  * If dataset is bigger than available memory:

    * Stream into the Dataset object **without persisting to disk**
    * Keep only one downloaded chunk/response section at a time
* No libraries allowed that create local cache layers implicitly:
  ❌ pyarrow local files, sqlite cache, disk-backed memory maps, joblib disk cache, HF hub cache.

#### 🔁 **Dataset Interface**

* Implement a main **`Dataset` class** that supports:

  * Construction from API download result
  * `__iter__()` to iterate over the loaded data items sequentially
  * Access to raw downloaded content
  * No `iter_batches()`, no lazy download iterators in this phase

---

### ⚙️ **Required Core API**

#### ✅ `load_dataset(dataset_id: str, config: Optional[dict] = None) -> Dataset`

* This function must:

  * Authenticate with the service
  * Call the dataset download API
  * Construct and return a Dataset object
  * Be the **only public SDK function** required in the MVP

#### ✅ `class Dataset`

Must include:

```python
class Dataset:
    def __init__(self, data):  # data is raw in-memory dataset response
        self.data = data

    def __iter__(self):
        for item in self.data:
            yield item
```

---

### 🧯 **Failure Handling Rules (MVP Specific)**

The SDK must:

* Raise simple built-in exceptions when failures occur
* Use clear error messages like:

  * `"Authentication failed: SERVICE_API_KEY or token missing or invalid"`
  * `"Dataset download failed after 3 retry attempts"`
  * `"Connection timeout: request exceeded 60 seconds"`
* No complex exception class hierarchy yet

---

### 🧪 **Testing Requirements**

Must include:

* A test file or test suite verifying:
  ✔ Service connection
  ✔ Authentication success/failure
  ✔ Dataset download completes
  ✔ Dataset iteration works and yields all items
* Mocking the service API is allowed for testing

---

### 📚 **Documentation Requirements (MVP Only)**

* Include a short README covering:

  * Installation steps (`pip install -e .`)
  * How to authenticate using env vars
  * How to call `load_dataset()`
  * Example of iterating the dataset
* No extended API reference or architecture docs yet

---

### 📦 **Local Installation Requirement**

* The SDK must install and run locally in dev mode
* Include minimal project structure:

  * `pyproject.toml` is optional for MVP but allowed if minimal
  * No publishing metadata yet
  * No dependency extras yet

---

### ✔ **Definition of Done — Milestone 1**

Your delivery is considered complete when:

| Requirement                                      | Status |
| ------------------------------------------------ | ------ |
| SDK installs locally (`pip install -e .`)        | ✅      |
| Authenticates with our dataset service API       | ✅      |
| Downloads dataset end-to-end reliably            | ✅      |
| Stores dataset fully **in memory only**          | ✅      |
| Dataset class supports `__iter__()`              | ✅      |
| `load_dataset()` returns Dataset object          | ✅      |
| No disk cache or local persistence of any kind   | ✅      |
| Test suite validates core integration flow       | ✅      |
| README shows working usage example               | ✅      |
| No lazy loading, batching, or ML conversions yet | ✅      |