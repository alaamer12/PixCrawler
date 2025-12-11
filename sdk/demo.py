import os
from unittest.mock import Mock, patch

import pixcrawler as pix


def main():
    print("PixCrawler SDK Demo")
    print("===================")

    # 1. Setup Environment
    # You would normally set these in your shell or .env file
    if not os.getenv("PIXCRAWLER_SERVICE_KEY"):
        print("Setting temporary API key for demo...")
        os.environ["PIXCRAWLER_SERVICE_KEY"] = "demo-key-123"

    # 2. Mocking for demonstration (Optional: remove this block to test against real API)
    print("[Demo] Network calls are mocked. To use real API, remove the mocking block in demo.py.\n")

    def mock_request(method, url, **kwargs):
        print(f"[Mock] {method} request to: {url}")
        print(f"[Mock] Headers: {kwargs.get('headers', {}).get('Authorization', 'None')}")

        response = Mock()
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        
        # Mock different endpoints
        if "/datasets" in url and "/export/json" in url:
            # Dataset export endpoint
            response.json.return_value = [
                {"id": "img_1", "url": "http://example.com/1.jpg", "label": "cat"},
                {"id": "img_2", "url": "http://example.com/2.jpg", "label": "dog"},
                {"id": "img_3", "url": "http://example.com/3.jpg", "label": "bird"},
            ]
        elif "/datasets/" in url and url.endswith(("/1", "/2", "/3")):
            # Individual dataset info
            dataset_id = url.split("/")[-1]
            response.json.return_value = {
                "id": int(dataset_id),
                "name": f"Demo Dataset {dataset_id}",
                "total_images": 100 + int(dataset_id) * 50,
                "size_mb": 25.5 + int(dataset_id) * 10,
                "status": "completed",
                "created_at": "2024-01-01T00:00:00Z"
            }
        elif "/datasets" in url:
            # List datasets
            response.json.return_value = {
                "items": [
                    {"id": 1, "name": "Cat Images", "total_images": 150, "status": "completed"},
                    {"id": 2, "name": "Dog Images", "total_images": 200, "status": "completed"},
                    {"id": 3, "name": "Bird Images", "total_images": 250, "status": "processing"}
                ],
                "total": 3,
                "page": 1,
                "size": 50
            }
        elif "/projects/" in url:
            # Project info
            project_id = url.split("/")[-1]
            response.json.return_value = {
                "id": int(project_id),
                "name": f"Demo Project {project_id}",
                "description": "A sample project for demonstration",
                "created_at": "2024-01-01T00:00:00Z"
            }
        else:
            response.json.return_value = {"message": "Mock response"}
        
        return response

    # Apply mock
    with patch('pixcrawler.core.requests.request', side_effect=mock_request):
        try:
            # Demo 1: Authentication
            print("1. Authentication Demo")
            print("----------------------")
            pix.auth(token="demo-api-key-123")
            print("✓ Authentication set globally\n")

            # Demo 2: List datasets
            print("2. List Datasets Demo")
            print("---------------------")
            datasets_list = pix.datasets(page=1, size=10)
            print(f"Found {len(datasets_list)} datasets:")
            for ds in datasets_list:
                print(f"  - {ds['id']}: {ds['name']} ({ds['total_images']} images)")
            print()

            # Demo 3: Dataset operations
            print("3. Dataset Operations Demo")
            print("--------------------------")
            
            # Get dataset info
            dataset = pix.dataset("1")
            info = dataset.info()
            print(f"Dataset Info: {info['name']}")
            print(f"  Images: {info['total_images']}")
            print(f"  Size: {info['size_mb']} MB")
            print(f"  Status: {info['status']}")
            
            # Load dataset into memory
            print("\nLoading dataset into memory...")
            dataset.load()
            print(f"✓ Dataset loaded with {len(dataset)} items")
            
            # Iterate over items
            print("\nFirst 3 items:")
            for i, item in enumerate(dataset):
                if i >= 3:
                    break
                print(f"  Item {i+1}: {item}")
            print()

            # Demo 4: Project operations
            print("4. Project Operations Demo")
            print("--------------------------")
            
            project = pix.project("123")
            project_info = project.info()
            print(f"Project: {project_info['name']}")
            print(f"Description: {project_info['description']}")
            
            # List datasets in project
            project_datasets = project.datasets()
            print(f"\nDatasets in project: {len(project_datasets)}")
            for ds in project_datasets:
                print(f"  - {ds['name']}")
            print()

            # Demo 5: Legacy functions
            print("5. Legacy Functions Demo")
            print("------------------------")
            
            # Legacy load_dataset function
            legacy_dataset = pix.load_dataset("2")
            print(f"✓ Legacy load_dataset works: {len(legacy_dataset)} items")
            
            # Legacy list_datasets function
            legacy_list = pix.list_datasets(page=1, size=5)
            print(f"✓ Legacy list_datasets works: {len(legacy_list)} datasets")
            print()

            print("🎉 All demos completed successfully!")
            print("\nTo use with real API:")
            print("1. Set PIXCRAWLER_SERVICE_KEY environment variable")
            print("2. Remove the mocking code from demo.py")
            print("3. Use your actual dataset and project IDs")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()