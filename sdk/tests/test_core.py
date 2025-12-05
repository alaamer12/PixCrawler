import pytest
from unittest.mock import Mock, patch
from sdk.pixcrawler import load_dataset, Dataset
import requests

@pytest.fixture
def mock_env_key(monkeypatch):
    monkeypatch.setenv("SERVICE_API_KEY", "test_key")

def test_dataset_iteration():
    data = [{"id": 1}, {"id": 2}, {"id": 3}]
    dataset = Dataset(data)
    items = list(dataset)
    assert items == data

@patch("pixcrawler.core.requests.get")
def test_load_dataset_success(mock_get, mock_env_key):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1}, {"id": 2}]
    mock_get.return_value = mock_response

    dataset = load_dataset("test-dataset")
    assert isinstance(dataset, Dataset)
    assert list(dataset) == [{"id": 1}, {"id": 2}]

    # Verify call
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "headers" in kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer test_key"

def test_load_dataset_no_auth():
    with pytest.raises(ValueError, match="Authentication failed"):
        # Ensure no env var
        with patch.dict("os.environ", {}, clear=True):
            load_dataset("test-dataset")

@patch("pixcrawler.core.requests.get")
def test_load_dataset_retry_success(mock_get, mock_env_key):
    # Fail twice, then succeed
    mock_fail = Mock()
    mock_fail.status_code = 503

    mock_success = Mock()
    mock_success.status_code = 200
    mock_success.json.return_value = []

    mock_get.side_effect = [mock_fail, mock_fail, mock_success]

    dataset = load_dataset("test-dataset")
    assert isinstance(dataset, Dataset)
    assert mock_get.call_count == 3

@patch("pixcrawler.core.requests.get")
def test_load_dataset_retry_failure(mock_get, mock_env_key):
    # Fail 3 times
    mock_fail = Mock()
    mock_fail.status_code = 503
    mock_get.return_value = mock_fail

    with pytest.raises(ConnectionError, match="Dataset download failed after 3 retry attempts"):
        load_dataset("test-dataset")

    assert mock_get.call_count == 3

@patch("pixcrawler.core.requests.get")
def test_load_dataset_timeout(mock_get, mock_env_key):
    mock_get.side_effect = requests.exceptions.Timeout

    with pytest.raises(TimeoutError, match="Connection timeout"):
        load_dataset("test-dataset")

    assert mock_get.call_count == 3

@patch("pixcrawler.core.requests.get")
def test_load_dataset_exceeds_memory_limit(mock_get, mock_env_key):
    # Create a mock response that exceeds 300MB
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": str(400 * 1024 * 1024)}  # 400MB
    mock_get.return_value = mock_response

    with pytest.raises(RuntimeError, match="exceeds memory limit"):
        load_dataset("test-dataset")
