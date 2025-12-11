#!/usr/bin/env python3
"""
Test the complete integration: Token Generation + Simple Flow System.
"""

import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def test_complete_integration():
    """Test the complete integration flow."""
    
    print("🚀 Testing Complete Integration")
    print("=" * 60)
    
    # Step 1: Generate API Token
    print("\n🔑 Step 1: Generating API Token...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/tokens/generate",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 201:
            token_data = response.json()
            api_token = token_data.get('token')
            print(f"   ✅ Token generated: {api_token[:20]}...")
        else:
            print(f"   ❌ Token generation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Token generation error: {e}")
        return False
    
    # Step 2: Start Simple Flow
    print(f"\n📋 Step 2: Starting Simple Flow...")
    
    flow_data = {
        "keywords": ["cat"],
        "max_images": 5,
        "engines": ["duckduckgo"],
        "output_name": "integration_test"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/simple-flow/start",
            json=flow_data,
            timeout=10
        )
        
        if response.status_code == 201:
            flow = response.json()
            flow_id = flow.get('flow_id')
            print(f"   ✅ Flow started: {flow_id}")
            print(f"   Output: {flow.get('output_path')}")
        else:
            print(f"   ❌ Flow creation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Flow creation error: {e}")
        return False
    
    # Step 3: Monitor Flow Progress
    print(f"\n📊 Step 3: Monitoring flow progress...")
    
    for i in range(15):
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/simple-flow/{flow_id}/status",
                timeout=5
            )
            
            if response.status_code == 200:
                status = response.json()
                
                print(f"   [{i+1:2}/15] {status.get('status'):12} | "
                      f"Progress: {status.get('progress', 0):3}% | "
                      f"Downloaded: {status.get('downloaded_images', 0):3}")
                
                if status.get('status') in ['completed', 'failed']:
                    print(f"   🏁 Flow finished: {status.get('status')}")
                    break
                    
        except Exception as e:
            print(f"   [{i+1:2}/15] ❌ Error: {e}")
        
        time.sleep(3)
    
    # Step 4: Check Output
    print(f"\n📂 Step 4: Checking output...")
    
    output_dir = "datasets/integration_test"
    
    if os.path.exists(output_dir):
        total_files = 0
        for root, dirs, files in os.walk(output_dir):
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            total_files += len(image_files)
            
            if image_files:
                print(f"   📁 {root}: {len(image_files)} images")
        
        print(f"   📊 Total images: {total_files}")
        files_created = total_files > 0
    else:
        print(f"   ❌ Output directory not found")
        files_created = False
    
    # Step 5: Show SDK Usage Example
    print(f"\n🐍 Step 5: SDK Usage Example...")
    print(f"   Token: {api_token}")
    print(f"   Flow ID: {flow_id}")
    
    sdk_example = f'''import pixcrawler as pix

# Set authentication (PIXCRAWLER_SERVICE_KEY)
pix.auth(token="{api_token}")

# Load dataset into memory
dataset = pix.load_dataset("{flow_id}")

# Iterate over items
for item in dataset:
    print(item)'''
    
    print("   Python Code:")
    print("   " + "="*50)
    for line in sdk_example.split('\n'):
        print(f"   {line}")
    print("   " + "="*50)
    
    # Final Results
    print(f"\n🎉 Integration Test Results:")
    print(f"   ✅ Token Generated: {api_token[:20]}...")
    print(f"   ✅ Flow Created: {flow_id}")
    print(f"   ✅ Images Downloaded: {files_created}")
    print(f"   ✅ SDK Example Ready")
    
    if files_created:
        print(f"\n   🎯 SUCCESS! Complete integration is working!")
        print(f"   📁 Images saved to: {output_dir}")
        print(f"   🔑 Use token: {api_token}")
        print(f"   📋 Load dataset: {flow_id}")
        return True
    else:
        print(f"\n   ⚠️  Integration partially working - no images downloaded")
        return False

if __name__ == "__main__":
    test_complete_integration()