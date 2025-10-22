"""
Local testing script for PixCrawler FastAPI.
Run this before deploying to Azure to ensure everything works.

Usage:
    python test_api_local.py
"""

import time
from typing import Dict, Any

import requests

BASE_URL = "http://localhost:8000"


def test_health() -> bool:
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed:", response.json())
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_generate_dataset() -> str:
    """Test dataset generation endpoint."""
    print("\n🔍 Testing dataset generation...")
    
    payload = {
        "dataset_name": "local_test",
        "categories": {
            "animals": ["cat"],
            "vehicles": ["car"]
        },
        "max_images": 3,
        "keyword_generation": "disabled",
        "generate_labels": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            job_id = data.get("job_id")
            print(f"✅ Generation started! Job ID: {job_id}")
            print(f"   Status: {data.get('status')}")
            return job_id
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_job_status(job_id: str) -> Dict[str, Any]:
    """Test job status endpoint."""
    print(f"\n🔍 Checking job status for {job_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            print(f"   Status: {status}")
            
            if status == "completed":
                print(f"✅ Job completed!")
                print(f"   Total images: {data.get('total_images')}")
                print(f"   Output dir: {data.get('output_dir')}")
            elif status == "failed":
                print(f"❌ Job failed!")
                print(f"   Error: {data.get('error')}")
            elif status == "running":
                print(f"⏳ Job still running...")
            
            return data
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_list_images(job_id: str) -> bool:
    """Test image listing endpoint."""
    print(f"\n🔍 Listing images for job {job_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/images/{job_id}")
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total_images", 0)
            images = data.get("images", [])
            
            print(f"✅ Found {total} images!")
            
            if images:
                print("\n📸 Sample images:")
                for img in images[:5]:  # Show first 5
                    print(f"   - {img.get('filename')} ({img.get('category')})")
                    print(f"     URL: {BASE_URL}{img.get('url')}")
                    print(f"     Size: {img.get('size_bytes')} bytes")
            
            return True
        else:
            print(f"❌ Image listing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_serve_image(job_id: str) -> bool:
    """Test image serving endpoint."""
    print(f"\n🔍 Testing image serving...")
    
    # First get the image list
    try:
        response = requests.get(f"{BASE_URL}/api/images/{job_id}")
        if response.status_code != 200:
            print("❌ Could not get image list")
            return False
        
        images = response.json().get("images", [])
        if not images:
            print("❌ No images to test")
            return False
        
        # Try to fetch the first image
        first_image_url = images[0].get("url")
        print(f"   Fetching: {BASE_URL}{first_image_url}")
        
        img_response = requests.get(f"{BASE_URL}{first_image_url}")
        
        if img_response.status_code == 200:
            print(f"✅ Image served successfully!")
            print(f"   Content-Type: {img_response.headers.get('content-type')}")
            print(f"   Size: {len(img_response.content)} bytes")
            return True
        else:
            print(f"❌ Image serving failed: {img_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 PixCrawler API Local Testing")
    print("=" * 60)
    print("\nMake sure the API is running:")
    print("  python api_main.py")
    print("\n" + "=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        print("   Start it with: python api_main.py")
        return
    
    # Test 2: Generate dataset
    job_id = test_generate_dataset()
    if not job_id:
        print("\n❌ Dataset generation failed. Check the logs.")
        return
    
    # Test 3: Wait for completion
    print("\n⏳ Waiting for job to complete (this may take 1-2 minutes)...")
    max_attempts = 60  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(5)  # Check every 5 seconds
        attempt += 1
        
        status_data = test_job_status(job_id)
        if not status_data:
            continue
        
        status = status_data.get("status")
        
        if status == "completed":
            break
        elif status == "failed":
            print("\n❌ Job failed. Check the error message above.")
            return
        
        if attempt % 6 == 0:  # Print progress every 30 seconds
            print(f"   Still waiting... ({attempt * 5}s elapsed)")
    
    if attempt >= max_attempts:
        print("\n⏰ Timeout waiting for job completion")
        return
    
    # Test 4: List images
    if not test_list_images(job_id):
        print("\n❌ Image listing failed")
        return
    
    # Test 5: Serve image
    if not test_serve_image(job_id):
        print("\n❌ Image serving failed")
        return
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n📋 Summary:")
    print("   ✅ Health check works")
    print("   ✅ Dataset generation works")
    print("   ✅ Job status tracking works")
    print("   ✅ Image listing works")
    print("   ✅ Image serving works")
    print("\n🚀 Ready for Azure deployment!")
    print("\nNext steps:")
    print("   1. Review AZURE_DEPLOYMENT.md")
    print("   2. Deploy to Azure using the guide")
    print("   3. Run the same tests against your Azure URL")


if __name__ == "__main__":
    main()
