"""
Test the SDK interface matches the README specification.
"""

import pytest
from unittest.mock import Mock, patch

import pixcrawler as pix


class TestSDKInterface:
    """Test that the SDK interface matches the README specification."""

    def test_imports(self):
        """Test that all expected functions and classes are importable."""
        # Core classes
        assert hasattr(pix, 'Dataset')
        assert hasattr(pix, 'Project')
        
        # Main functions
        assert hasattr(pix, 'auth')
        assert hasattr(pix, 'dataset')
        assert hasattr(pix, 'datasets')
        assert hasattr(pix, 'project')
        assert hasattr(pix, 'get_dataset_info')
        assert hasattr(pix, 'download_dataset')
        
        # Legacy functions
        assert hasattr(pix, 'load_dataset')
        assert hasattr(pix, 'list_datasets')
        
        # Exceptions
        assert hasattr(pix, 'PixCrawlerError')
        assert hasattr(pix, 'APIError')
        assert hasattr(pix, 'AuthenticationError')
        assert hasattr(pix, 'NotFoundError')
        assert hasattr(pix, 'RateLimitError')

    def test_auth_function(self):
        """Test the auth function sets global authentication."""
        pix.auth(token="test-token", base_url="https://test.api.com")
        
        # Verify global state is set
        from pixcrawler.core import _global_auth_token, _global_base_url
        assert _global_auth_token == "test-token"
        assert _global_base_url == "https://test.api.com"

    @patch('pixcrawler.core.requests.request')
    def test_dataset_class(self, mock_request):
        """Test Dataset class functionality."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "name": "Test Dataset",
            "total_images": 100,
            "size_mb": 25.5,
            "status": "completed"
        }
        mock_request.return_value = mock_response
        
        # Test dataset creation and info
        dataset = pix.dataset("123")
        assert dataset.dataset_id == "123"
        
        info = dataset.info()
        assert info["name"] == "Test Dataset"
        assert dataset.name == "Test Dataset"
        assert dataset.image_count == 100
        assert dataset.size_mb == 25.5

    @patch('pixcrawler.core.requests.request')
    def test_dataset_load(self, mock_request):
        """Test Dataset load functionality."""
        # Mock export JSON response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = [
            {"id": 1, "url": "http://example.com/1.jpg", "label": "cat"},
            {"id": 2, "url": "http://example.com/2.jpg", "label": "dog"}
        ]
        mock_request.return_value = mock_response
        
        dataset = pix.dataset("123")
        loaded_dataset = dataset.load()
        
        # Should return self for chaining
        assert loaded_dataset is dataset
        
        # Should be iterable
        items = list(dataset)
        assert len(items) == 2
        assert items[0]["label"] == "cat"
        assert items[1]["label"] == "dog"

    @patch('pixcrawler.core.requests.request')
    def test_project_class(self, mock_request):
        """Test Project class functionality."""
        # Mock project info response
        def mock_request_side_effect(method, url, **kwargs):
            response = Mock()
            response.status_code = 200
            
            if "/projects/" in url:
                response.json.return_value = {
                    "id": 456,
                    "name": "Test Project",
                    "description": "A test project"
                }
            elif "/datasets" in url:
                response.json.return_value = {
                    "items": [
                        {"id": 1, "name": "Dataset 1"},
                        {"id": 2, "name": "Dataset 2"}
                    ]
                }
            return response
        
        mock_request.side_effect = mock_request_side_effect
        
        project = pix.project("456")
        assert project.project_id == "456"
        
        info = project.info()
        assert info["name"] == "Test Project"
        assert project.name == "Test Project"
        assert project.description == "A test project"
        
        datasets_list = project.datasets()
        assert len(datasets_list) == 2
        assert datasets_list[0]["name"] == "Dataset 1"

    @patch('pixcrawler.core.requests.request')
    def test_datasets_function(self, mock_request):
        """Test the datasets function."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"id": 1, "name": "Dataset 1", "total_images": 100},
                {"id": 2, "name": "Dataset 2", "total_images": 200}
            ],
            "total": 2,
            "page": 1,
            "size": 50
        }
        mock_request.return_value = mock_response
        
        pix.auth(token="test-token")
        datasets_list = pix.datasets(page=1, size=10)
        
        assert len(datasets_list) == 2
        assert datasets_list[0]["name"] == "Dataset 1"
        assert datasets_list[1]["total_images"] == 200

    @patch('pixcrawler.core.requests.request')
    def test_get_dataset_info_function(self, mock_request):
        """Test the get_dataset_info function."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 789,
            "name": "Info Dataset",
            "total_images": 500,
            "size_mb": 125.0
        }
        mock_request.return_value = mock_response
        
        info = pix.get_dataset_info("789")
        assert info["name"] == "Info Dataset"
        assert info["total_images"] == 500

    def test_legacy_functions_exist(self):
        """Test that legacy functions exist for backward compatibility."""
        # These should be callable (even if they fail without mocking)
        assert callable(pix.load_dataset)
        assert callable(pix.list_datasets)

    def test_exception_hierarchy(self):
        """Test that exceptions have proper hierarchy."""
        # All custom exceptions should inherit from PixCrawlerError
        assert issubclass(pix.APIError, pix.PixCrawlerError)
        assert issubclass(pix.AuthenticationError, pix.PixCrawlerError)
        assert issubclass(pix.NotFoundError, pix.PixCrawlerError)
        assert issubclass(pix.RateLimitError, pix.PixCrawlerError)
        assert issubclass(pix.ValidationError, pix.PixCrawlerError)

    @patch('pixcrawler.core.requests.request')
    def test_error_handling(self, mock_request):
        """Test that API errors are properly handled."""
        # Test 404 error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        with pytest.raises(pix.NotFoundError):
            pix.get_dataset_info("nonexistent")
        
        # Test 401 error
        mock_response.status_code = 401
        with pytest.raises(pix.AuthenticationError):
            pix.datasets()
        
        # Test 429 error
        mock_response.status_code = 429
        with pytest.raises(pix.RateLimitError):
            pix.datasets()

    def test_readme_examples_syntax(self):
        """Test that README examples have valid syntax."""
        # This tests the basic syntax of README examples
        
        # Example 1: Basic usage
        try:
            # This should not raise syntax errors
            code = """
import pixcrawler as pix
pix.auth(token="your_api_key")
project = pix.project("project-id")
dataset = project.dataset("dataset-id-123")
"""
            compile(code, '<string>', 'exec')
        except SyntaxError:
            pytest.fail("README example 1 has syntax errors")
        
        # Example 2: Dataset operations
        try:
            code = """
import pixcrawler as pix
dataset = pix.dataset("dataset-id-123")
info = dataset.info()
data = dataset.load()
path = dataset.download("./my_dataset.zip")
"""
            compile(code, '<string>', 'exec')
        except SyntaxError:
            pytest.fail("README example 2 has syntax errors")