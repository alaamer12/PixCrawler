#!/usr/bin/env python3
"""
Test the simple flow system.
"""

import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IlVpZkx5YzF4d3FQMnBSaTUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3lmZGFkcGdzeHVkZm96Z2RlZmdzLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyY2RkNTE3OC0yNmM2LTQ5ZTAtODdhYi03MjZiZTQ1ZTNmNWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY1NDU0MDQ0LCJpYXQiOjE3NjU0NTA0NDQsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IkpvaG4gRG9lIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiIyY2RkNTE3OC0yNmM2LTQ5ZTAtODdhYi03MjZiZTQ1ZTNmNWEifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc2NTQ1MDQ0NH1dLCJzZXNzaW9uX2lkIjoiMDllMGIzOTUtNTAzNC00Yjg2LWEwODEtZGY5MTUyOThlOTVhIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.2zmrdvSrAFpHNLIMd4QBMh79cO0uGL9dB74PEM8X_aw"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_flow_system():
    """Test the simple flow system."""
    
    print("🚀 Testing Simple Flow System")
    print("=" * 50)
    
    # Step 1: Start a flow
    print("\n📋 Step 1: Starting flow...")
    
    flow_data = {
        "keywords": ["cat", "dog"],
        "max_images": 10,
        "engines": ["duckduckgo"],
        "output_name": "test_simple_flow"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simple-flow/start",
            headers=headers,
            json=flow_data,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            flow = response.json()
            flow_id = flow.get('flow_id')
            print(f"   ✅ Flow started: {flow_id}")
            print(f"   Output: {flow.get('output_path')}")
            print(f"   Tasks: {len(flow.get('task_ids', []))}")
            
            return flow_id
        else:
            print(f"   ❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def monitor_flow(flow_id):
    """Monitor flow progress."""
    
    print(f"\n📊 Step 2: Monitoring flow {flow_id}...")
    
    for i in range(20):  # Monitor for 20 iterations
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/simple-flow/{flow_id}/status",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                status = response.json()
                
                print(f"   [{i+1:2}/20] {status.get('status'):12} | "
                      f"Progress: {status.get('progress', 0):3}% | "
                      f"Downloaded: {status.get('downloaded_images', 0):3} | "
                      f"Tasks: {status.get('completed_tasks', 0)}/{status.get('total_tasks', 0)}")
                
                # Check if completed
                if status.get('status') in ['completed', 'failed']:
                    print(f"   🏁 Flow finished: {status.get('status')}")
                    return status.get('status')
                    
            else:
                print(f"   [{i+1:2}/20] ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   [{i+1:2}/20] ❌ Error: {e}")
        
        time.sleep(3)
    
    return "monitoring_timeout"

def get_flow_result(flow_id):
    """Get final flow result."""
    
    print(f"\n📁 Step 3: Getting flow result...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/simple-flow/{flow_id}/result",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"   ✅ Flow completed!")
            print(f"   Downloaded: {result.get('total_downloaded', 0)} images")
            print(f"   Output: {result.get('output_path')}")
            print(f"   Total size: {result.get('total_size_mb', 0)} MB")
            print(f"   Processing time: {result.get('processing_time', 0):.1f}s")
            
            # Show some files
            files = result.get('file_list', [])
            if files:
                print(f"   📋 Sample files:")
                for i, file_info in enumerate(files[:5]):
                    print(f"     {i+1}. {file_info.get('filename')} ({file_info.get('size_mb')} MB)")
            
            return True
        else:
            print(f"   ❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_output_directory(flow_id):
    """Check if output directory was created."""
    
    print(f"\n📂 Step 4: Checking output directory...")
    
    output_dir = f"datasets/test_simple_flow"
    
    if os.path.exists(output_dir):
        print(f"   ✅ Output directory exists: {output_dir}")
        
        # Count files
        total_files = 0
        for root, dirs, files in os.walk(output_dir):
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            total_files += len(image_files)
            
            if image_files:
                print(f"   📁 {root}: {len(image_files)} images")
        
        print(f"   📊 Total images: {total_files}")
        return total_files > 0
    else:
        print(f"   ❌ Output directory not found: {output_dir}")
        return False

def main():
    """Run the flow test."""
    
    print("🧪 Testing Simple Flow System")
    print("=" * 60)
    
    # Test flow creation and start
    flow_id = test_flow_system()
    
    if not flow_id:
        print("❌ Flow creation failed!")
        return
    
    # Monitor progress
    final_status = monitor_flow(flow_id)
    
    # Get results
    if final_status in ['completed', 'monitoring_timeout']:
        success = get_flow_result(flow_id)
        files_exist = check_output_directory(flow_id)
    else:
        success = False
        files_exist = False
    
    print(f"\n🎉 Test Results:")
    print(f"   Flow ID: {flow_id}")
    print(f"   Final Status: {final_status}")
    print(f"   API Success: {success}")
    print(f"   Files Created: {files_exist}")
    
    if success and files_exist:
        print(f"   ✅ SUCCESS! Simple Flow system is working perfectly!")
        print(f"   📁 Check datasets/test_simple_flow/ for images")
        print(f"   🎯 This proves the system can generate real datasets!")
    else:
        print(f"   ❌ Flow system needs debugging")
        if not success:
            print(f"      - API calls failed")
        if not files_exist:
            print(f"      - No files were created")

if __name__ == "__main__":
    main()