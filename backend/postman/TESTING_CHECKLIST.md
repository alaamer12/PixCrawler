# Postman Collection Testing Checklist

Quick reference for testing the PixCrawler Frontend Mock collection.

## Pre-Testing Setup

- [ ] Prism mock server is running: `prism mock backend/postman/openapi.json -p 4010`
- [ ] Postman collection imported
- [ ] {{baseUrl}} variable set to `http://localhost:4010/api/v1`
- [ ] Server responds to health check: `curl http://localhost:4010/api/v1/health/`

---

## Quick Test Checklist

### 1. Crawl Jobs (6/27)
- [ ] 1.1 Create Crawl Job (POST /jobs/) → 201
- [ ] 1.2 Get Job Details (GET /jobs/{id}) → 200
- [ ] 1.3 Start Job (POST /jobs/{id}/start) → 200
- [ ] 1.4 Cancel Job (POST /jobs/{id}/cancel) → 200
- [ ] 1.5 Retry Failed Job (POST /jobs/{id}/retry) → 200
- [ ] 1.6 Get Job Progress (GET /jobs/{id}/progress) → 200

### 2. Validation (6/27)
- [ ] 2.1 Analyze Single Image (POST /validation/analyze/) → 200
- [ ] 2.2 Create Batch Validation (POST /validation/batch/) → 201
- [ ] 2.3 Validate Job Images (POST /validation/job/{id}/) → 200
- [ ] 2.4 Get Validation Results (GET /validation/results/{id}/) → 200
- [ ] 2.5 Get Dataset Validation Stats (GET /validation/stats/{id}/) → 200
- [ ] 2.6 Update Validation Level (PUT /validation/level/) → 200

### 3. Credits & Billing (4/27)
- [ ] 3.1 Get Credit Balance (GET /credits/balance) → 200
- [ ] 3.2 List Credit Transactions (GET /credits/transactions) → 200
- [ ] 3.3 Purchase Credits (POST /credits/purchase) → 201
- [ ] 3.4 Get Usage Metrics (GET /credits/usage) → 200

### 4. API Keys (4/27)
- [ ] 4.1 List API Keys (GET /api-keys/) → 200
- [ ] 4.2 Create API Key (POST /api-keys/) → 201
- [ ] 4.3 Revoke API Key (DELETE /api-keys/{id}) → 200
- [ ] 4.4 Get API Key Usage (GET /api-keys/{id}/usage) → 200

### 5. Storage (4/27)
- [ ] 5.1 Get Storage Usage (GET /storage/usage/) → 200
- [ ] 5.2 List Storage Files (GET /storage/files/) → 200
- [ ] 5.3 Initiate Storage Cleanup (POST /storage/cleanup/) → 200
- [ ] 5.4 Generate Presigned URL (GET /storage/presigned-url/) → 200

### 6. Activity Logs (1/27)
- [ ] 6.1 List Activity Logs (GET /activity/) → 200

### 7. Health Checks (2/27)
- [ ] 7.1 Basic Health Check (GET /health/) → 200
- [ ] 7.2 Detailed Health Check (GET /health/detailed) → 200

---

## Quick Validation Checks

For each endpoint, verify:
- [ ] Status code is 200 or 201
- [ ] Response has `{"data": {...}}` or `{"data": [...], "meta": {...}}` structure
- [ ] All timestamps are ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ)
- [ ] All IDs are valid UUIDs
- [ ] {{baseUrl}} variable is substituted correctly
- [ ] Response matches OpenAPI example

---

## One-Line Test Commands

```bash
# Health Check
curl http://localhost:4010/api/v1/health/

# Create Job
curl -X POST http://localhost:4010/api/v1/jobs/ -H "Content-Type: application/json" -d '{"project_id":"550e8400-e29b-41d4-a716-446655440000","name":"Test","keywords":["laptop"],"max_images":1000}'

# Get Job
curl http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002

# Start Job
curl -X POST http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002/start -H "Content-Type: application/json"

# Get Progress
curl http://localhost:4010/api/v1/jobs/770e8400-e29b-41d4-a716-446655440002/progress

# Analyze Image
curl -X POST http://localhost:4010/api/v1/validation/analyze/ -H "Content-Type: application/json" -d '{"image_url":"https://example.com/image.jpg"}'

# Get Balance
curl http://localhost:4010/api/v1/credits/balance

# List API Keys
curl http://localhost:4010/api/v1/api-keys/

# Get Storage Usage
curl http://localhost:4010/api/v1/storage/usage/

# List Activity
curl http://localhost:4010/api/v1/activity/?page=1&limit=20
```

---

## Automated Test

Run all tests at once:
```bash
cd backend/postman
chmod +x test_all_endpoints.sh
./test_all_endpoints.sh
```

---

## Test Summary

**Total Endpoints:** 27  
**Tested:** ___ / 27  
**Passed:** ___ / 27  
**Failed:** ___ / 27  

**Status:** ☐ All Pass / ☐ Some Fail / ☐ Not Started

---

## Issues Found

```
[List any issues here]
```

---

## Sign-Off

**Tester:** ___________  
**Date:** ___________  
**Ready for Production:** ☐ Yes / ☐ No
