🎯 **Python Dataset Loader SDK — Milestone-Based Delivery**

You are a senior Python SDK engineer responsible for delivering a reliable **Python SDK library** for dataset loading.

The development must be delivered in **two structured milestones**:

---

### **Milestone 1: ✅ MVP Phase**

**Objective:** Deliver a minimal, fully working **MVP SDK** that conforms to core integration requirements and nothing beyond the MVP scope.

The SDK must:

* Integrate successfully with **our internal service API**
* Authenticate using the provided service credentials
* Download a dataset from our service
* Assemble the dataset **in-memory**
* Expose a basic iterable **Dataset class**
* Provide the `load_dataset()` function as the only required entry point

🚫 **Do NOT implement any of the following in this phase:**

* Lazy loading
* Parallel downloads
* ML framework conversions
* Disk caching
* Batch iteration utilities
* Packaging for PyPI
* Advanced memory optimizations
* Custom exceptions tree
* Performance features
* Extended documentation

**Definition of Done:**
✔ SDK installs locally
✔ SDK connects & authenticates with our service
✔ Dataset downloads end-to-end with no failures
✔ `Dataset` object can iterate over downloaded data

---

### **Milestone 2: 🚀 Full SDK Enhancement Phase**

**Objective:** Expand the SDK into a production-grade library by implementing all advanced capabilities previously defined (lazy streaming, parallel downloads, ML integration, error handling, testing, documentation, and packaging).

This includes:

* Efficient lazy/loading strategies
* Parallel chunk downloading with retries
* ML framework conversion interfaces (NumPy, PyTorch, TensorFlow, sklearn)
* Structured error hierarchy and exceptions
* Memory guardrails
* Test coverage across SDK and ML integrations
* Full professional documentation
* Proper packaging and PyPI readiness

**Definition of Done:**
✔ All features implemented, validated, and tested
✔ ML integrations functional
✔ Memory consumption optimized
✔ Full documentation complete
✔ Package builds and is publish-ready