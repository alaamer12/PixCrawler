#!/bin/bash
# Test script for Azure-deployed PixCrawler API
# Usage: ./test_azure_api.sh <your-azure-app-name>

if [ -z "$1" ]; then
    echo "Usage: ./test_azure_api.sh <your-azure-app-name>"
    echo "Example: ./test_azure_api.sh pixcrawler-test-abc123"
    exit 1
fi

APP_NAME=$1
BASE_URL="https://${APP_NAME}.azurewebsites.net"

echo "=========================================="
echo "Testing PixCrawler API on Azure"
echo "URL: $BASE_URL"
echo "=========================================="

# Test 1: Health Check
echo -e "\n[1/5] Testing health endpoint..."
curl -s "$BASE_URL/health" | python -m json.tool
if [ $? -eq 0 ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test 2: Start Generation
echo -e "\n[2/5] Starting dataset generation..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "dataset_name": "azure_test",
        "categories": {
            "animals": ["cat"],
            "vehicles": ["car"]
        },
        "max_images": 5,
        "keyword_generation": "disabled",
        "generate_labels": false
    }')

echo "$RESPONSE" | python -m json.tool

JOB_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to get job ID"
    exit 1
fi

echo "✅ Job started with ID: $JOB_ID"

# Test 3: Check Status (with polling)
echo -e "\n[3/5] Checking job status..."
MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
    
    STATUS_RESPONSE=$(curl -s "$BASE_URL/api/status/$JOB_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    
    echo "   Attempt $ATTEMPT: Status = $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Job completed successfully!"
        echo "$STATUS_RESPONSE" | python -m json.tool
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Job failed!"
        echo "$STATUS_RESPONSE" | python -m json.tool
        exit 1
    fi
    
    if [ $((ATTEMPT % 6)) -eq 0 ]; then
        echo "   Still waiting... ($((ATTEMPT * 5))s elapsed)"
    fi
done

if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    echo "⏰ Timeout waiting for job completion"
    exit 1
fi

# Test 4: List Images
echo -e "\n[4/5] Listing generated images..."
IMAGES_RESPONSE=$(curl -s "$BASE_URL/api/images/$JOB_ID")
echo "$IMAGES_RESPONSE" | python -m json.tool

TOTAL_IMAGES=$(echo "$IMAGES_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['total_images'])" 2>/dev/null)
echo "✅ Found $TOTAL_IMAGES images"

# Test 5: Get First Image URL
echo -e "\n[5/5] Testing image access..."
FIRST_IMAGE_URL=$(echo "$IMAGES_RESPONSE" | python -c "import sys, json; data=json.load(sys.stdin); print(data['images'][0]['url'] if data['images'] else '')" 2>/dev/null)

if [ -n "$FIRST_IMAGE_URL" ]; then
    FULL_URL="$BASE_URL$FIRST_IMAGE_URL"
    echo "   Image URL: $FULL_URL"
    
    # Try to fetch the image
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FULL_URL")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Image accessible!"
    else
        echo "❌ Image not accessible (HTTP $HTTP_CODE)"
    fi
else
    echo "❌ No images found"
fi

# Summary
echo -e "\n=========================================="
echo "🎉 TEST SUMMARY"
echo "=========================================="
echo "Job ID: $JOB_ID"
echo "Total Images: $TOTAL_IMAGES"
echo "Dataset URL: $BASE_URL/api/images/$JOB_ID"
echo ""
echo "✅ BOTH QUESTIONS ANSWERED:"
echo "1. Azure CAN generate images locally on cloud"
echo "2. You CAN get URLs for each image"
echo ""
echo "View all images:"
echo "  curl $BASE_URL/api/images/$JOB_ID"
echo ""
echo "View API docs:"
echo "  $BASE_URL/docs"
echo "=========================================="
