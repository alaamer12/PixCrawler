# Storage Service Test Suite

Comprehensive unit and integration tests for the PixCrawler backend storage service.

## 📋 Overview

This test suite ensures the reliability and correctness of the storage service through:
- **Unit Tests**: Individual component testing with isolated behavior verification
- **Integration Tests**: End-to-end workflows and cross-component interactions
- **Performance Tests**: Throughput and scalability validation
- **Security Tests**: Path traversal prevention and access control

## 🗂️ Test Structure

```
backend/tests/
├── test_storage_unit.py           # Unit tests for storage providers
├── test_storage_integration.py    # Integration tests for workflows
├── conftest.py                     # Shared fixtures and configuration
└── README_STORAGE_TESTS.md        # This file
```

## 🧪 Test Coverage

### Unit Tests (`test_storage_unit.py`)

#### LocalStorageProvider Tests
- **Initialization**
  - Custom directory creation
  - Platformdirs integration
  - Path normalization
  
- **Upload Operations**
  - File upload with metadata preservation
  - Subdirectory creation
  - File overwriting
  - Error handling (missing files, invalid paths)
  
- **Download Operations**
  - File download with directory creation
  - Overwrite handling
  - Error propagation
  
- **Delete Operations**
  - File deletion
  - Parent directory preservation
  - Error handling
  
- **List Operations**
  - Empty storage handling
  - Prefix filtering
  - Sorted results
  - Cross-platform path handling
  
- **Presigned URL Generation**
  - URL generation with expiration
  - Custom expiry times
  - Special character encoding
  
- **Security**
  - Directory traversal prevention (upload, download, delete)
  - Absolute path rejection
  - Path validation

#### StorageSettings Tests
- Default configuration values
- Provider validation (local, azure)
- Azure connection string requirements
- Container name validation
- Tier and priority validation
- Lifecycle policy validation
- Path normalization

### Integration Tests (`test_storage_integration.py`)

#### Factory Integration
- Provider creation from settings
- Environment variable loading
- Default settings handling
- Error handling for invalid configurations

#### End-to-End Workflows
- **Complete Dataset Workflow**
  - Upload multiple files
  - Organization by category
  - Selective download
  - Presigned URL generation
  - Cleanup operations
  
- **Multi-Project Isolation**
  - Isolated storage per project
  - Prefix-based filtering
  - Cross-project verification
  
- **Backup and Restore**
  - Full backup creation
  - Data loss simulation
  - Complete restoration
  
- **Versioning**
  - Multiple file versions
  - Version backup
  - Current version tracking

#### Configuration Integration
- Environment variable loading
- Validation in integration context
- Various configuration scenarios

#### Error Recovery
- Partial upload recovery
- Missing file handling
- Corrupted operation handling

#### Performance Tests
- Large file operations (1MB+)
- Many small files (100+)
- Sequential operation performance
- Large directory listing

#### Real-World Scenarios
- Image dataset management
- Temporary file cleanup
- User quota simulation

## 🚀 Running Tests

### Run All Storage Tests
```bash
# From backend directory
pytest tests/test_storage_unit.py tests/test_storage_integration.py -v

# Or with coverage
pytest tests/test_storage_unit.py tests/test_storage_integration.py --cov=backend.storage --cov-report=html
```

### Run Specific Test Classes
```bash
# Unit tests only
pytest tests/test_storage_unit.py -v

# Integration tests only
pytest tests/test_storage_integration.py -v

# Specific test class
pytest tests/test_storage_unit.py::TestLocalStorageProviderUpload -v

# Specific test method
pytest tests/test_storage_unit.py::TestLocalStorageProviderUpload::test_upload_file_success -v
```

### Run Tests by Markers
```bash
# Run only unit tests (if marked)
pytest tests/ -m unit -v

# Run only integration tests (if marked)
pytest tests/ -m integration -v

# Run slow tests
pytest tests/ -m slow -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

### Run with Different Verbosity
```bash
# Minimal output
pytest tests/test_storage_unit.py -q

# Verbose output
pytest tests/test_storage_unit.py -v

# Very verbose (show all test names)
pytest tests/test_storage_unit.py -vv
```

### Run with Coverage Report
```bash
# Terminal coverage report
pytest tests/test_storage_unit.py --cov=backend.storage --cov-report=term-missing

# HTML coverage report
pytest tests/test_storage_unit.py --cov=backend.storage --cov-report=html

# XML coverage report (for CI/CD)
pytest tests/test_storage_unit.py --cov=backend.storage --cov-report=xml
```

## 📊 Test Metrics

### Expected Coverage
- **Unit Tests**: >95% code coverage
- **Integration Tests**: >85% workflow coverage
- **Overall**: >90% combined coverage

### Performance Benchmarks
- Single file upload: <100ms
- Single file download: <100ms
- List 100 files: <1s
- Large file (1MB) operations: <1s
- 100 small file uploads: <5s

## 🔧 Test Configuration

### Environment Variables
Tests use isolated temporary directories and don't require external services:

```bash
# Optional: Override storage path for tests
export STORAGE_LOCAL_STORAGE_PATH=/tmp/pixcrawler_test_storage

# Optional: Enable test logging
export PIXCRAWLER_LOG_LEVEL=DEBUG
```

### Fixtures
Key fixtures available in `conftest.py`:
- `temp_dir`: Temporary directory for test files
- `local_storage`: LocalStorageProvider instance
- `sample_file`: Sample text file
- `sample_image`: Sample PNG image
- `test_files_dir`: Directory with various test files
- `local_storage_settings`: Pre-configured StorageSettings

## 🐛 Debugging Tests

### Run with Print Statements
```bash
pytest tests/test_storage_unit.py -s
```

### Run with PDB Debugger
```bash
pytest tests/test_storage_unit.py --pdb
```

### Run Failed Tests Only
```bash
# Run tests, then re-run only failures
pytest tests/test_storage_unit.py
pytest tests/test_storage_unit.py --lf
```

### Show Local Variables on Failure
```bash
pytest tests/test_storage_unit.py -l
```

## 📝 Writing New Tests

### Test Naming Convention
- Test files: `test_storage_*.py`
- Test classes: `Test<Component><Feature>`
- Test methods: `test_<action>_<scenario>`

Example:
```python
class TestLocalStorageProviderUpload:
    def test_upload_file_success(self, local_storage, sample_file):
        """Test successful file upload."""
        # Arrange
        destination = "uploads/test.txt"
        
        # Act
        local_storage.upload(sample_file, destination)
        
        # Assert
        uploaded_file = local_storage.base_directory / destination
        assert uploaded_file.exists()
```

### Test Structure (AAA Pattern)
1. **Arrange**: Set up test data and conditions
2. **Act**: Execute the operation being tested
3. **Assert**: Verify the expected outcome

### Using Fixtures
```python
@pytest.fixture
def custom_fixture(temp_dir):
    """Create custom test data."""
    # Setup
    data = create_test_data(temp_dir)
    yield data
    # Teardown (optional)
    cleanup_test_data(data)
```

## 🔍 Test Categories

### Unit Tests
- Focus on single component behavior
- Use mocks for external dependencies
- Fast execution (<1s per test)
- Isolated from file system when possible

### Integration Tests
- Test component interactions
- Use real file system operations
- Moderate execution time (1-5s per test)
- Verify end-to-end workflows

### Performance Tests
- Measure operation throughput
- Validate scalability
- May take longer to execute
- Use realistic data volumes

## ✅ Test Quality Checklist

- [ ] Test has clear, descriptive name
- [ ] Test follows AAA pattern
- [ ] Test is isolated (no dependencies on other tests)
- [ ] Test cleans up resources (uses fixtures or teardown)
- [ ] Test has docstring explaining purpose
- [ ] Test covers both success and failure cases
- [ ] Test assertions are specific and meaningful
- [ ] Test is deterministic (no random behavior)

## 🚨 Common Issues

### Issue: Tests fail due to permission errors
**Solution**: Ensure test directories are writable. On Unix systems, check file permissions.

### Issue: Tests are slow
**Solution**: Use `pytest -v --durations=10` to identify slow tests. Consider marking slow tests with `@pytest.mark.slow`.

### Issue: Temp directory cleanup fails
**Solution**: Ensure all file handles are closed. Use context managers or explicit cleanup in fixtures.

### Issue: Path separator issues (Windows vs Unix)
**Solution**: Always use `Path` objects and forward slashes in storage paths. The storage provider handles conversion.

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/mark.html)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## 🤝 Contributing

When adding new storage features:
1. Write unit tests for new methods
2. Add integration tests for new workflows
3. Update this README with new test coverage
4. Ensure all tests pass before submitting PR
5. Maintain >90% code coverage

## 📈 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Storage Tests
  run: |
    pytest backend/tests/test_storage_unit.py \
           backend/tests/test_storage_integration.py \
           --cov=backend.storage \
           --cov-report=xml \
           --junitxml=test-results.xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

### Test Execution Order
1. Unit tests (fast, isolated)
2. Integration tests (moderate speed)
3. Performance tests (slower, optional in PR checks)

## 📞 Support

For questions or issues with tests:
- Check existing test examples
- Review pytest documentation
- Ask in team chat or create an issue
- Refer to project coding guidelines
