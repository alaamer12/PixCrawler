# Storage Tests - Quick Start Guide

Get started with running storage tests in under 5 minutes.

## 🚀 Quick Commands

### Run All Storage Tests
```bash
# From backend directory
pytest tests/test_storage_unit.py tests/test_storage_integration.py -v
```

### Run with Coverage
```bash
pytest tests/test_storage_unit.py tests/test_storage_integration.py --cov=backend.storage --cov-report=html
```

### Using the Test Runner Script
```bash
# Run all tests
python tests/run_storage_tests.py

# Run only unit tests
python tests/run_storage_tests.py --unit

# Run only integration tests
python tests/run_storage_tests.py --integration

# Run with coverage
python tests/run_storage_tests.py --coverage --html
```

## 📋 Prerequisites

### Install Dependencies
```bash
# From project root
pip install -e backend[dev]

# Or with uv
uv pip install -e backend[dev]
```

### Required Packages
- pytest >= 8.4.1
- pytest-asyncio >= 1.2.0
- pytest-cov >= 7.0.0
- pytest-mock (optional, for advanced mocking)

## ✅ Verify Installation

```bash
# Check pytest is installed
pytest --version

# Run a quick smoke test
pytest tests/test_storage_unit.py::TestLocalStorageProviderInit::test_init_with_custom_directory -v
```

## 📊 Test Results

### Expected Output
```
tests/test_storage_unit.py::TestLocalStorageProviderInit::test_init_with_custom_directory PASSED [100%]

========================== 1 passed in 0.05s ===========================
```

### Coverage Report
After running with `--cov`, open the HTML report:
```bash
# Windows
start htmlcov/storage/index.html

# Linux/Mac
open htmlcov/storage/index.html
```

## 🎯 Common Test Scenarios

### Test Specific Feature
```bash
# Test upload operations only
pytest tests/test_storage_unit.py::TestLocalStorageProviderUpload -v

# Test a specific method
pytest tests/test_storage_unit.py::TestLocalStorageProviderUpload::test_upload_file_success -v
```

### Run Fast Tests Only
```bash
pytest tests/test_storage_unit.py tests/test_storage_integration.py -m "not slow" -v
```

### Debug Failed Tests
```bash
# Show print statements
pytest tests/test_storage_unit.py -s

# Drop into debugger on failure
pytest tests/test_storage_unit.py --pdb

# Show local variables
pytest tests/test_storage_unit.py -l
```

## 🔍 Understanding Test Output

### Test Status Symbols
- `.` - Test passed
- `F` - Test failed
- `E` - Test error
- `s` - Test skipped
- `x` - Expected failure
- `X` - Unexpected pass

### Verbose Output
```
tests/test_storage_unit.py::TestLocalStorageProviderUpload::test_upload_file_success PASSED [1/50]
tests/test_storage_unit.py::TestLocalStorageProviderUpload::test_upload_creates_subdirectories PASSED [2/50]
...
```

## 🐛 Troubleshooting

### Issue: "No module named 'backend'"
**Solution**: Install backend package in development mode:
```bash
pip install -e backend
```

### Issue: "Permission denied" errors
**Solution**: Tests use temporary directories. Ensure you have write permissions:
```bash
# Check temp directory
python -c "import tempfile; print(tempfile.gettempdir())"
```

### Issue: Tests are slow
**Solution**: Run unit tests only (faster):
```bash
pytest tests/test_storage_unit.py -v
```

### Issue: Import errors
**Solution**: Ensure you're in the correct directory:
```bash
# Should be in backend directory
cd backend
pytest tests/test_storage_unit.py -v
```

## 📈 Next Steps

1. **Read Full Documentation**: See `README_STORAGE_TESTS.md` for comprehensive guide
2. **Run Integration Tests**: `pytest tests/test_storage_integration.py -v`
3. **Check Coverage**: Aim for >90% coverage
4. **Write New Tests**: Follow patterns in existing test files

## 💡 Pro Tips

### Run Tests on File Change
```bash
# Install pytest-watch
pip install pytest-watch

# Auto-run tests on changes
ptw tests/test_storage_unit.py -- -v
```

### Parallel Execution
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/test_storage_unit.py -n auto
```

### Generate JUnit XML (for CI/CD)
```bash
pytest tests/test_storage_unit.py --junitxml=test-results.xml
```

## 🎓 Learning Resources

- **Test Examples**: Look at existing tests in `test_storage_unit.py`
- **Fixtures**: Check `conftest.py` for reusable test fixtures
- **Pytest Docs**: https://docs.pytest.org/
- **Coverage Docs**: https://coverage.readthedocs.io/

## 📞 Need Help?

- Check test output for specific error messages
- Review test documentation in `README_STORAGE_TESTS.md`
- Look at similar tests for patterns
- Ask team members or create an issue

---

**Happy Testing! 🧪**
