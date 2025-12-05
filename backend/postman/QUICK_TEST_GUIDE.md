# Quick Test Guide - Postman Collection

This guide provides quick curl commands to test all 27 endpoints in the PixCrawler Frontend Mock collection against the Prism mock server.

## Prerequisites

1. **Start Prism Mock Server:**
   ```bash
   prism mock backend/postman/openapi.json -p 4010
   ```

2. **Verify Server is Running:**
   ```bash
   curl http://localhost:4010/api/v1/health/
   ```

---

## Quick Test Commands

### 1. Crawl Jobs (6 endpoints)

#### 1.1 Create Crawl Job
```bash
curl -X POST http://localhost:4010/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Laptop Product Images",
    "keywords": ["laptop", "computer", "notebook"],
    "max_images": 1000,
    "engines": ["google", "bing", "duckduckgo"],
    "quality_filters": {
      "min_resolution": [224, 224],
      "formats": ["jpg", "png", "webp"]
    }
  }'
```
**Expected:** 201 Created with job object

#### 1.2 Get Job Details
```bash
curl http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002
```
**Expected:** 200 OK with job details

#### 1.3 Start Job
```bash
curl -X POST http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002/start \
  -H "Content-Type: application/json"
```
**Expected:** 200 OK with task_ids array

#### 1.4 Cancel Job
```bash
curl -X POST http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002/cancel \
  -H "Content-Type: application/json"
```
**Expected:** 200 OK with revoked_count

#### 1.5 Retry Failed Job
```bash
curl -X POST http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002/retry \
  -H "Content-Type: application/json"
```
**Expected:** 200 OK with new task_ids

#### 1.6 Get Job Progress
```bash
curl http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002/progress
```
**Expected:** 200 OK with progress metrics

---

### 2. Validation (6 endpoints)

#### 2.1 Analyze Single Image
```bash
curl -X POST http://localhost:4010/api/v1/validation/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/images/laptop.jpg"}'
```
**Expected:** 200 OK with validation results

#### 2.2 Create Batch Validation
```bash
curl -X POST http://localhost:4010/api/v1/validation/batch/ \
  -H "Content-Type: application/json" \
  -d '{
    "image_ids": [
      "880e8400-e29b-41d4-a716-446655440010",
      "880e8400-e29b-41d4-a716-446655440011",
      "880e8400-e29b-41d4-a716-446655440012"
    ],
    "validation_level": "medium"
  }'
```
**Expected:** 201 Created with batch_id

#### 2.3 Validate Job Images
```bash
curl -X POST http://localhost:4010/api/v1/validation/job/770e8400-e29b-41d4-a716-446655440002/ \
  -H "Content-Type: application/json" \
  -d '{"validation_level": "medium"}'
```
**Expected:** 200 OK with task_ids

#### 2.4 Get Validation Results
```bash
curl http://localhost:4010/api/v1/validation/results/770e8400-e29b-41d4-a716-446655440002/
```
**Expected:** 200 OK with aggregated stats

#### 2.5 Get Dataset Validation Stats
```bash
curl http://localhost:4010/api/v1/validation/stats/aa0e8400-e29b-41d4-a716-446655440030/
```
**Expected:** 200 OK with validation coverage

#### 2.6 Update Validation Level
```bash
curl -X PUT http://localhost:4010/api/v1/validation/level/ \
  -H "Content-Type: application/json" \
  -d '{"level": "medium"}'
```
**Expected:** 200 OK with confirmation

---

### 3. Credits & Billing (4 endpoints)

#### 3.1 Get Credit Balance
```bash
curl http://localhost:4010/api/v1/credits/balance
```
**Expected:** 200 OK with balance info

#### 3.2 List Credit Transactions
```bash
curl "http://localhost:4010/api/v1/credits/transactions?page=1&limit=20"
```
**Expected:** 200 OK with paginated transactions

#### 3.3 Purchase Credits
```bash
curl -X POST http://localhost:4010/api/v1/credits/purchase \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000,
    "payment_method": "lemonsqueezy",
    "payment_token": "order_abc123"
  }'
```
**Expected:** 201 Created with transaction details

#### 3.4 Get Usage Metrics
```bash
curl "http://localhost:4010/api/v1/credits/usage?start_date=2025-12-01&end_date=2025-12-05&granularity=daily"
```
**Expected:** 200 OK with daily metrics

---

### 4. API Keys (4 endpoints)

#### 4.1 List API Keys
```bash
curl http://localhost:4010/api/v1/api-keys/
```
**Expected:** 200 OK with API keys list

#### 4.2 Create API Key
```bash
curl -X POST http://localhost:4010/api/v1/api-keys/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "permissions": ["read", "write"],
    "rate_limit": 1000,
    "expires_at": "2026-12-05T00:00:00Z"
  }'
```
**Expected:** 201 Created with full key value

#### 4.3 Revoke API Key
```bash
curl -X DELETE http://localhost:4010/api/v1/api-keys/cc0e8400-e29b-41d4-a716-446655440050
```
**Expected:** 200 OK with revocation confirmation

#### 4.4 Get API Key Usage
```bash
curl http://localhost:4010/api/v1/api-keys/cc0e8400-e29b-41d4-a716-446655440050/usage
```
**Expected:** 200 OK with usage statistics

---

### 5. Storage (4 endpoints)

#### 5.1 Get Storage Usage
```bash
curl http://localhost:4010/api/v1/storage/usage/
```
**Expected:** 200 OK with storage breakdown

#### 5.2 List Storage Files
```bash
curl "http://localhost:4010/api/v1/storage/files/?page=1&limit=20"
```
**Expected:** 200 OK with paginated file list

#### 5.3 Initiate Storage Cleanup
```bash
curl -X POST http://localhost:4010/api/v1/storage/cleanup/ \
  -H "Content-Type: application/json" \
  -d '{
    "older_than_days": 30,
    "tier": "warm"
  }'
```
**Expected:** 200 OK with deleted_count

#### 5.4 Generate Presigned URL
```bash
curl "http://localhost:4010/api/v1/storage/presigned-url/?file_path=datasets/770e8400-e29b-41d4-a716-446655440002/dataset_770e8400_images.zip&expires_in=3600"
```
**Expected:** 200 OK with presigned URL

---

### 6. Activity Logs (1 endpoint)

#### 6.1 List Activity Logs
```bash
curl "http://localhost:4010/api/v1/activity/?page=1&limit=20"
```
**Expected:** 200 OK with paginated activity logs

---

### 7. Health Checks (2 endpoints)

#### 7.1 Basic Health Check
```bash
curl http://localhost:4010/api/v1/health/
```
**Expected:** 200 OK with basic health status

#### 7.2 Detailed Health Check
```bash
curl http://localhost:4010/api/v1/health/detailed
```
**Expected:** 200 OK with service-level health

---

## Automated Test Script

Save this as `test_all_endpoints.sh`:

```bash
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:4010/api/v1"
PASSED=0
FAILED=0

echo "Testing PixCrawler Frontend Mock API..."
echo "========================================"
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local path=$3
    local data=$4
    
    echo -n "Testing $name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$path")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$path" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASS${NC} ($status_code)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} ($status_code)"
        ((FAILED++))
    fi
}

# Crawl Jobs
echo "1. Crawl Jobs"
test_endpoint "Create Crawl Job" "POST" "/jobs/" '{"project_id":"550e8400-e29b-41d4-a716-446655440000","name":"Test Job","keywords":["laptop"],"max_images":1000}'
test_endpoint "Get Job Details" "GET" "/jobs/770e8400-e29b-41d4-a716-446655440002"
test_endpoint "Start Job" "POST" "/jobs/770e8400-e29b-41d4-a716-446655440002/start"
test_endpoint "Cancel Job" "POST" "/jobs/770e8400-e29b-41d4-a716-446655440002/cancel"
test_endpoint "Retry Job" "POST" "/jobs/770e8400-e29b-41d4-a716-446655440002/retry"
test_endpoint "Get Job Progress" "GET" "/jobs/770e8400-e29b-41d4-a716-446655440002/progress"
echo ""

# Validation
echo "2. Validation"
test_endpoint "Analyze Image" "POST" "/validation/analyze/" '{"image_url":"https://example.com/image.jpg"}'
test_endpoint "Create Batch Validation" "POST" "/validation/batch/" '{"image_ids":["880e8400-e29b-41d4-a716-446655440010"],"validation_level":"medium"}'
test_endpoint "Validate Job Images" "POST" "/validation/job/770e8400-e29b-41d4-a716-446655440002/" '{"validation_level":"medium"}'
test_endpoint "Get Validation Results" "GET" "/validation/results/770e8400-e29b-41d4-a716-446655440002/"
test_endpoint "Get Dataset Stats" "GET" "/validation/stats/aa0e8400-e29b-41d4-a716-446655440030/"
test_endpoint "Update Validation Level" "PUT" "/validation/level/" '{"level":"medium"}'
echo ""

# Credits & Billing
echo "3. Credits & Billing"
test_endpoint "Get Credit Balance" "GET" "/credits/balance"
test_endpoint "List Transactions" "GET" "/credits/transactions?page=1&limit=20"
test_endpoint "Purchase Credits" "POST" "/credits/purchase" '{"amount":1000,"payment_method":"lemonsqueezy","payment_token":"order_abc123"}'
test_endpoint "Get Usage Metrics" "GET" "/credits/usage?start_date=2025-12-01&end_date=2025-12-05&granularity=daily"
echo ""

# API Keys
echo "4. API Keys"
test_endpoint "List API Keys" "GET" "/api-keys/"
test_endpoint "Create API Key" "POST" "/api-keys/" '{"name":"Test Key","permissions":["read","write"],"rate_limit":1000}'
test_endpoint "Revoke API Key" "DELETE" "/api-keys/cc0e8400-e29b-41d4-a716-446655440050"
test_endpoint "Get API Key Usage" "GET" "/api-keys/cc0e8400-e29b-41d4-a716-446655440050/usage"
echo ""

# Storage
echo "5. Storage"
test_endpoint "Get Storage Usage" "GET" "/storage/usage/"
test_endpoint "List Storage Files" "GET" "/storage/files/?page=1&limit=20"
test_endpoint "Initiate Cleanup" "POST" "/storage/cleanup/" '{"older_than_days":30,"tier":"warm"}'
test_endpoint "Generate Presigned URL" "GET" "/storage/presigned-url/?file_path=datasets/test.zip&expires_in=3600"
echo ""

# Activity Logs
echo "6. Activity Logs"
test_endpoint "List Activity Logs" "GET" "/activity/?page=1&limit=20"
echo ""

# Health Checks
echo "7. Health Checks"
test_endpoint "Basic Health Check" "GET" "/health/"
test_endpoint "Detailed Health Check" "GET" "/health/detailed"
echo ""

# Summary
echo "========================================"
echo "Test Summary:"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
```

Make it executable:
```bash
chmod +x test_all_endpoints.sh
```

Run it:
```bash
./test_all_endpoints.sh
```

---

## Postman Import Instructions

1. **Open Postman**
2. **Click "Import"** button (top left)
3. **Select "File"** tab
4. **Choose** `backend/postman/PixCrawler_Frontend_Mock.json`
5. **Click "Import"**
6. **Verify** collection appears in left sidebar
7. **Check** {{baseUrl}} variable is set correctly:
   - Click on collection name
   - Go to "Variables" tab
   - Verify `baseUrl` = `http://localhost:4010/api/v1`

---

## Testing Tips

1. **Start with Health Checks** - Verify mock server is working
2. **Test in Order** - Follow the folder order for logical flow
3. **Check Response Structure** - Verify `{"data": {...}}` format
4. **Validate Data Types** - Ensure UUIDs, timestamps, numbers are correct
5. **Test {{baseUrl}} Variable** - Verify it's substituted in all URLs
6. **Compare with OpenAPI** - Ensure responses match OpenAPI examples
7. **Document Issues** - Note any discrepancies in test report

---

## Common Issues

### Issue: Connection Refused
**Solution:** Ensure Prism mock server is running on port 4010

### Issue: 404 Not Found
**Solution:** Check URL path matches OpenAPI spec exactly (trailing slashes matter)

### Issue: Invalid JSON Response
**Solution:** Verify OpenAPI spec has valid example data

### Issue: {{baseUrl}} Not Substituted
**Solution:** Ensure variable is defined in collection and environment

---

## Next Steps

After completing testing:
1. Fill out `POSTMAN_COLLECTION_TEST_REPORT.md`
2. Fix any issues found
3. Re-test failed endpoints
4. Mark Task 14 as complete
5. Proceed to Task 15 (Update README.md)
