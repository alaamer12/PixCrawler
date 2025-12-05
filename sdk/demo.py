import os

from pixcrawler import load_dataset


# Mock the requests.get to avoid actual network calls if needed,
# or set up a real environment.
# For this demo, we will assume the user might want to run it against a real or mocked service.
# If no service is running, we can mock it here for demonstration purposes.

def main():
    print("PixCrawler SDK Demo")
    print("-------------------")

    # 1. Setup Environment
    # You would normally set these in your shell or .env file
    if not os.getenv("SERVICE_API_KEY"):
        print("Setting temporary API key for demo...")
        os.environ["SERVICE_API_KEY"] = "demo-key-123"

    # 2. Mocking for demonstration (Optional: remove this block to test against real API)
    # We monkeypatch requests.get to simulate a successful response
    import requests
    from unittest.mock import Mock

    original_get = requests.get

    def mock_get(*args, **kwargs):
        print(f"[Mock] Intercepted GET request to: {args[0]}")
        print(f"[Mock] Headers: {kwargs.get('headers')}")

        # Simulate success
        response = Mock()
        response.status_code = 200
        response.json.return_value = [
            {"id": "img_1", "url": "http://example.com/1.jpg", "label": "cat"},
            {"id": "img_2", "url": "http://example.com/2.jpg", "label": "dog"},
            {"id": "img_3", "url": "http://example.com/3.jpg", "label": "bird"},
        ]
        return response

    # Apply mock
    requests.get = mock_get
    print("[Demo] Network calls are mocked. To use real API, remove the mocking block in demo.py.\n")

    # 3. Load Dataset
    try:
        print("Loading dataset 'test-dataset-001'...")
        dataset = load_dataset("test-dataset-001")
        print("Dataset loaded successfully!")

        # 4. Iterate
        print("\nIterating over dataset items:")
        for i, item in enumerate(dataset):
            print(f"Item {i+1}: {item}")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
