#!/usr/bin/env python3
"""
Test the complete system with backend + celery workers.
"""

import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def test_complete_system():
    """Test the complete system."""
    
    print("🚀 Testing Complete System (Backend + Celery)")
    print("=" * 60)
    
    # Step 1: Start a flow
    print("\n📋 Step 1: Starting flow...")
    
    flow_data = {
        "keywords": ["cat"],
        "max_images": 5,
        "engines": ["duckduckgo"],
        "output_name": "test_complete_system"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simple-flow/start",
            json=flow_data,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            flow = response.json()
            flow_id = flow.get('flow_id')
            print(f"   ✅ Flow started: {flow_id}")
            print(f"   Output: {flow.get('output_path')}")
            print(f"   Tasks: {flow.get('task_count')}")
            
            # Step 2: Monitor progress
            print(f"\n📊 Step 2: Monitoring flow {flow_id}...")
            
            for i in range(20):  # Monitor for 20 iterations
                try:
                    response = requests.get(
                        f"{BASE_URL}/api/v1/simple-flow/{flow_id}/status",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        status = response.json()
                        
                        print(f"   [{i+1:2}/20] {status.get('status'):12} | "
                              f"Progress: {status.get('progress', 0):3}% | "
                              f"Downloaded: {status.get('downloaded_images', 0):3}")
                        
                        # Check if completed
                        if status.get('status') in ['completed', 'failed']:
                            print(f"   🏁 Flow finished: {status.get('status')}")
                            break
                            
                    else:
                        print(f"   [{i+1:2}/20] ❌ Error: {response.status_code}")
                        
                except Exception as e:
                    print(f"   [{i+1:2}/20] ❌ Error: {e}")
                
                time.sleep(5)  # Wait 5 seconds between checks
            
            # Step 3: Check output directory
            print(f"\n📂 Step 3: Checking output directory...")
            
            output_dir = "datasets/test_complete_system"
            
            if os.path.exists(output_dir):
                print(f"   ✅ Output directory exists: {output_dir}")
                
                # Count files
                total_files = 0
                for root, dirs, files in os.walk(output_dir):
                    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                    total_files += len(image_files)
                    
                    if image_files:
                        print(f"   📁 {root}: {len(image_files)} images")
                        # Show first few files
                        for img in image_files[:3]:
                            print(f"     - {img}")
                
                print(f"   📊 Total images: {total_files}")
                
                if total_files > 0:
                    print(f"\n   ✅ SUCCESS! Complete system is working!")
                    print(f"   🎯 Images were successfully downloaded and saved!")
                    print(f"   📁 Check {output_dir} for the images")
                else:
                    print(f"\n   ⚠️  No images found yet - may need more time")
            else:
                print(f"   ❌ Output directory not found: {output_dir}")
            
        else:
            print(f"   ❌ Failed to start flow: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_complete_system()