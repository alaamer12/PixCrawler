# Prism Mock Server Testing Guide

## Overview

This guide provides instructions for testing the OpenAPI specification using Prism mock server. The testing validates that all 27 endpoints are properly defined and return expected responses.

## Prerequisites

### Required Software

1. **Node.js** (v18.0.0 or higher)
   - Download from: https://nodejs.org/
   - Verify installation: `node --version`

2. **Prism CLI**
   - Install globally: `npm install -g @stoplight/prism-cli`
   - Verify installation: `prism --version`

### Alternative: Using npx (No Installation Required)

If you don't want to install Prism globally, you can use npx:
```bash
npx @stoplight/prism-cli mock backend/postman/openapi.json -p 4010
```

## Installation Steps

### Step 1: Install Prism CLI

```bash
# Using npm (recommended)
npm install -g @stoplight/prism-cli

# Using yarn
yarn global add @stoplight/prism-cli

# Using bun
bun add -g @stoplight/prism-cli
```

### Step 2: Verify Installation

```bash
prism --version
# Expected output: 5.x.x or higher
```

## Starting the Mock Server

### Basic Command

```bash
prism mock backend/postman/openapi.json -p 4010
```

### With Verbose Logging

```bash
prism mock backend/postman/openapi.json -p 4010 --verbose
```

### With Dynamic Response Selection

```bash
prism mock backend/postman/openapi.json -p 4010 --dynamic
```

### Expected Output

When the server starts successfully, you should see:
```
[CLI] …  awaiting  Starting Prism…
[CLI] ℹ  info      GET        http://127.0.0.1:4010/api/v1/jobs
[CLI] ℹ  info      POST       http://127.0.0.1:4010/api/v1/jobs
[CLI] ℹ  info      GET        http://127.0.0.1:4010/api/v1/jobs/{job_id}
... (all endpoints listed)
[CLI] ▶  start     Prism is listening on http://127.0.0.1:4010
```

## Testing Endpoints

### Test Script

Save this as `test-prism-endpoints.sh` (Linux/Mac) or `test-prism-endpoints.ps1` (Windows):

#### Bash Script (test-prism-endpoints.sh)

```bash
#!/bin/bash

BASE_URL="http://localhost:4010/api/v1"
PASSED=0
FAILED=0

echo "Testing PixCrawler Mock API Endpoints"
echo "======================================"
echo ""

# Function to test endpoint
test_endpoint() {
    local method=$1
    local path=$2
    local description=$3
    local data=$4
    
    echo -n "Testing: $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$path")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$path" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL$path" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" = "DELETE" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE_URL$path")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "✓ PASSED (HTTP $http_code)"
        ((PASSED++))
    else
        echo "✗ FAILED (HTTP $http_code)"
        ((FAILED++))
    fi
}

# Crawl Jobs Endpoints (6)
echo "Crawl Jobs Endpoints"
echo "--------------------"
test_endpoint "POST" "/jobs/" "Create crawl job" '{"project_id":"550e8400-e29b-41d4-a716-446655440000","name":"Test Job","keywords":["test"],"max_images":100}'
test_endpoint "GET" "/jobs/550e8400-e29b-41d4-a716-446655440000" "Get job details"
test_endpoint "POST" "/jobs/550e8400-e29b-41d4-a716-446655440000/start" "Start job"
test_endpoint "POST" "/jobs/550e8400-e29b-41d4-a716-446655440000/cancel" "Cancel job"
test_endpoint "POST" "/jobs/550e8400-e29b-41d4-a716-446655440000/retry" "Retry job"
test_endpoint "GET" "/jobs/550e8400-e29b-41d4-a716-446655440000/progress" "Get job progress"
echo ""

# Validation Endpoints (6)
echo "Validation Endpoints"
echo "--------------------"
test_endpoint "POST" "/validation/analyze/" "Analyze single image" '{"image_url":"https://example.com/image.jpg"}'
test_endpoint "POST" "/validation/batch/" "Create batch validation" '{"image_ids":["550e8400-e29b-41d4-a716-446655440000"],"validation_level":"medium"}'
test_endpoint "POST" "/validation/job/550e8400-e29b-41d4-a716-446655440000/" "Validate job images" '{"validation_level":"medium"}'
test_endpoint "GET" "/validation/results/550e8400-e29b-41d4-a716-446655440000/" "Get validation results"
test_endpoint "GET" "/validation/stats/550e8400-e29b-41d4-a716-446655440000/" "Get dataset validation stats"
test_endpoint "PUT" "/validation/level/" "Update validation level" '{"level":"fast"}'
echo ""

# Credits and Billing Endpoints (4)
echo "Credits and Billing Endpoints"
echo "------------------------------"
test_endpoint "GET" "/credits/balance" "Get credit balance"
test_endpoint "GET" "/credits/transactions" "List transactions"
test_endpoint "POST" "/credits/purchase" "Purchase credits" '{"amount":1000,"payment_method":"lemonsqueezy"}'
test_endpoint "GET" "/credits/usage" "Get usage metrics"
echo ""

# API Keys Management Endpoints (4)
echo "API Keys Management Endpoints"
echo "------------------------------"
test_endpoint "GET" "/api-keys/" "List API keys"
test_endpoint "POST" "/api-keys/" "Create API key" '{"name":"Test Key","permissions":["read"]}'
test_endpoint "DELETE" "/api-keys/550e8400-e29b-41d4-a716-446655440000" "Revoke API key"
test_endpoint "GET" "/api-keys/550e8400-e29b-41d4-a716-446655440000/usage" "Get key usage"
echo ""

# Storage Management Endpoints (4)
echo "Storage Management Endpoints"
echo "-----------------------------"
test_endpoint "GET" "/storage/usage/" "Get storage usage"
test_endpoint "GET" "/storage/files/" "List storage files"
test_endpoint "POST" "/storage/cleanup/" "Initiate cleanup" '{"older_than_days":30}'
test_endpoint "GET" "/storage/presigned-url/?file_path=test.zip" "Generate presigned URL"
echo ""

# Activity Logging Endpoints (1)
echo "Activity Logging Endpoints"
echo "--------------------------"
test_endpoint "GET" "/activity/" "List activity logs"
echo ""

# Health Check Endpoints (2)
echo "Health Check Endpoints"
echo "----------------------"
test_endpoint "GET" "/health/" "Basic health check"
test_endpoint "GET" "/health/detailed" "Detailed health check"
echo ""

# Summary
echo "======================================"
echo "Test Summary"
echo "======================================"
echo "Total Tests: $((PASSED + FAILED))"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi
```

#### PowerShell Script (test-prism-endpoints.ps1)

```powershell
$BaseUrl = "http://localhost:4010/api/v1"
$Passed = 0
$Failed = 0

Write-Host "Testing PixCrawler Mock API Endpoints" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Path,
        [string]$Description,
        [string]$Data = $null
    )
    
    Write-Host -NoNewline "Testing: $Description... "
    
    try {
        $uri = "$BaseUrl$Path"
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        if ($Method -eq "GET") {
            $response = Invoke-WebRequest -Uri $uri -Method GET -UseBasicParsing
        }
        elseif ($Method -eq "POST") {
            $response = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -Body $Data -UseBasicParsing
        }
        elseif ($Method -eq "PUT") {
            $response = Invoke-WebRequest -Uri $uri -Method PUT -Headers $headers -Body $Data -UseBasicParsing
        }
        elseif ($Method -eq "DELETE") {
            $response = Invoke-WebRequest -Uri $uri -Method DELETE -UseBasicParsing
        }
        
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq 200 -or $statusCode -eq 201) {
            Write-Host "✓ PASSED (HTTP $statusCode)" -ForegroundColor Green
            $script:Passed++
        }
        else {
            Write-Host "✗ FAILED (HTTP $statusCode)" -ForegroundColor Red
            $script:Failed++
        }
    }
    catch {
        Write-Host "✗ FAILED ($($_.Exception.Message))" -ForegroundColor Red
        $script:Failed++
    }
}

# Crawl Jobs Endpoints (6)
Write-Host "Crawl Jobs Endpoints" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow
Test-Endpoint -Method "POST" -Path "/jobs/" -Description "Create crawl job" -Data '{"project_id":"550e8400-e29b-41d4-a716-446655440000","name":"Test Job","keywords":["test"],"max_images":100}'
Test-Endpoint -Method "GET" -Path "/jobs/550e8400-e29b-41d4-a716-446655440000" -Description "Get job details"
Test-Endpoint -Method "POST" -Path "/jobs/550e8400-e29b-41d4-a716-446655440000/start" -Description "Start job"
Test-Endpoint -Method "POST" -Path "/jobs/550e8400-e29b-41d4-a716-446655440000/cancel" -Description "Cancel job"
Test-Endpoint -Method "POST" -Path "/jobs/550e8400-e29b-41d4-a716-446655440000/retry" -Description "Retry job"
Test-Endpoint -Method "GET" -Path "/jobs/550e8400-e29b-41d4-a716-446655440000/progress" -Description "Get job progress"
Write-Host ""

# Validation Endpoints (6)
Write-Host "Validation Endpoints" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Yellow
Test-Endpoint -Method "POST" -Path "/validation/analyze/" -Description "Analyze single image" -Data '{"image_url":"https://example.com/image.jpg"}'
Test-Endpoint -Method "POST" -Path "/validation/batch/" -Description "Create batch validation" -Data '{"image_ids":["550e8400-e29b-41d4-a716-446655440000"],"validation_level":"medium"}'
Test-Endpoint -Method "POST" -Path "/validation/job/550e8400-e29b-41d4-a716-446655440000/" -Description "Validate job images" -Data '{"validation_level":"medium"}'
Test-Endpoint -Method "GET" -Path "/validation/results/550e8400-e29b-41d4-a716-446655440000/" -Description "Get validation results"
Test-Endpoint -Method "GET" -Path "/validation/stats/550e8400-e29b-41d4-a716-446655440000/" -Description "Get dataset validation stats"
Test-Endpoint -Method "PUT" -Path "/validation/level/" -Description "Update validation level" -Data '{"level":"fast"}'
Write-Host ""

# Credits and Billing Endpoints (4)
Write-Host "Credits and Billing Endpoints" -ForegroundColor Yellow
Write-Host "------------------------------" -ForegroundColor Yellow
Test-Endpoint -Method "GET" -Path "/credits/balance" -Description "Get credit balance"
Test-Endpoint -Method "GET" -Path "/credits/transactions" -Description "List transactions"
Test-Endpoint -Method "POST" -Path "/credits/purchase" -Description "Purchase credits" -Data '{"amount":1000,"payment_method":"lemonsqueezy"}'
Test-Endpoint -Method "GET" -Path "/credits/usage" -Description "Get usage metrics"
Write-Host ""

# API Keys Management Endpoints (4)
Write-Host "API Keys Management Endpoints" -ForegroundColor Yellow
Write-Host "------------------------------" -ForegroundColor Yellow
Test-Endpoint -Method "GET" -Path "/api-keys/" -Description "List API keys"
Test-Endpoint -Method "POST" -Path "/api-keys/" -Description "Create API key" -Data '{"name":"Test Key","permissions":["read"]}'
Test-Endpoint -Method "DELETE" -Path "/api-keys/550e8400-e29b-41d4-a716-446655440000" -Description "Revoke API key"
Test-Endpoint -Method "GET" -Path "/api-keys/550e8400-e29b-41d4-a716-446655440000/usage" -Description "Get key usage"
Write-Host ""

# Storage Management Endpoints (4)
Write-Host "Storage Management Endpoints" -ForegroundColor Yellow
Write-Host "-----------------------------" -ForegroundColor Yellow
Test-Endpoint -Method "GET" -Path "/storage/usage/" -Description "Get storage usage"
Test-Endpoint -Method "GET" -Path "/storage/files/" -Description "List storage files"
Test-Endpoint -Method "POST" -Path "/storage/cleanup/" -Description "Initiate cleanup" -Data '{"older_than_days":30}'
Test-Endpoint -Method "GET" -Path "/storage/presigned-url/?file_path=test.zip" -Description "Generate presigned URL"
Write-Host ""

# Activity Logging Endpoints (1)
Write-Host "Activity Logging Endpoints" -ForegroundColor Yellow
Write-Host "--------------------------" -ForegroundColor Yellow
Test-Endpoint -Method "GET" -Path "/activity/" -Description "List activity logs"
Write-Host ""

# Health Check Endpoints (2)
Write-Host "Health Check Endpoints" -ForegroundColor Yellow
Write-Host "----------------------" -ForegroundColor Yellow
Test-Endpoint -Method "GET" -Path "/health/" -Description "Basic health check"
Test-Endpoint -Method "GET" -Path "/health/detailed" -Description "Detailed health check"
Write-Host ""

# Summary
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Total Tests: $($Passed + $Failed)"
Write-Host "Passed: $Passed" -ForegroundColor Green
Write-Host "Failed: $Failed" -ForegroundColor Red
Write-Host ""

if ($Failed -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "✗ Some tests failed" -ForegroundColor Red
    exit 1
}
```

## Manual Testing with curl

### Crawl Jobs Endpoints

```bash
# Create crawl job
curl -X POST http://localhost:4010/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"project_id":"550e8400-e29b-41d4-a716-446655440000","name":"Test Job","keywords":["laptop"],"max_images":100}'

# Get job details
curl http://localhost:4010/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000

# Start job
curl -X POST http://localhost:4010/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/start

# Cancel job
curl -X POST http://localhost:4010/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/cancel

# Retry job
curl -X POST http://localhost:4010/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/retry

# Get job progress
curl http://localhost:4010/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/progress
```

### Validation Endpoints

```bash
# Analyze single image
curl -X POST http://localhost:4010/api/v1/validation/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://example.com/image.jpg"}'

# Create batch validation
curl -X POST http://localhost:4010/api/v1/validation/batch/ \
  -H "Content-Type: application/json" \
  -d '{"image_ids":["550e8400-e29b-41d4-a716-446655440000"],"validation_level":"medium"}'

# Validate job images
curl -X POST http://localhost:4010/api/v1/validation/job/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Content-Type: application/json" \
  -d '{"validation_level":"medium"}'

# Get validation results
curl http://localhost:4010/api/v1/validation/results/550e8400-e29b-41d4-a716-446655440000/

# Get dataset validation stats
curl http://localhost:4010/api/v1/validation/stats/550e8400-e29b-41d4-a716-446655440000/

# Update validation level
curl -X PUT http://localhost:4010/api/v1/validation/level/ \
  -H "Content-Type: application/json" \
  -d '{"level":"fast"}'
```

### Credits and Billing Endpoints

```bash
# Get credit balance
curl http://localhost:4010/api/v1/credits/balance

# List transactions
curl http://localhost:4010/api/v1/credits/transactions

# Purchase credits
curl -X POST http://localhost:4010/api/v1/credits/purchase \
  -H "Content-Type: application/json" \
  -d '{"amount":1000,"payment_method":"lemonsqueezy"}'

# Get usage metrics
curl http://localhost:4010/api/v1/credits/usage
```

### API Keys Management Endpoints

```bash
# List API keys
curl http://localhost:4010/api/v1/api-keys/

# Create API key
curl -X POST http://localhost:4010/api/v1/api-keys/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Key","permissions":["read"]}'

# Revoke API key
curl -X DELETE http://localhost:4010/api/v1/api-keys/550e8400-e29b-41d4-a716-446655440000

# Get key usage
curl http://localhost:4010/api/v1/api-keys/550e8400-e29b-41d4-a716-446655440000/usage
```

### Storage Management Endpoints

```bash
# Get storage usage
curl http://localhost:4010/api/v1/storage/usage/

# List storage files
curl http://localhost:4010/api/v1/storage/files/

# Initiate cleanup
curl -X POST http://localhost:4010/api/v1/storage/cleanup/ \
  -H "Content-Type: application/json" \
  -d '{"older_than_days":30}'

# Generate presigned URL
curl "http://localhost:4010/api/v1/storage/presigned-url/?file_path=test.zip"
```

### Activity Logging Endpoints

```bash
# List activity logs
curl http://localhost:4010/api/v1/activity/
```

### Health Check Endpoints

```bash
# Basic health check
curl http://localhost:4010/api/v1/health/

# Detailed health check
curl http://localhost:4010/api/v1/health/detailed
```

## Validation Checklist

When testing, verify the following for each endpoint:

- [ ] Server starts without errors
- [ ] Endpoint returns 200 or 201 status code
- [ ] Response has correct Content-Type (application/json)
- [ ] Response structure matches OpenAPI schema
- [ ] All required fields are present
- [ ] Timestamps use ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ)
- [ ] UUIDs use valid UUID v4 format
- [ ] Paginated responses include meta object
- [ ] Response follows {"data": {...}} or {"data": [...], "meta": {...}} structure

## Troubleshooting

### Server Won't Start

**Problem**: `Error: Cannot find module '@stoplight/prism-cli'`
**Solution**: Install Prism CLI globally: `npm install -g @stoplight/prism-cli`

**Problem**: `Error: EADDRINUSE: address already in use :::4010`
**Solution**: Port 4010 is already in use. Either:
- Stop the process using port 4010
- Use a different port: `prism mock backend/postman/openapi.json -p 4011`

### Invalid OpenAPI Spec

**Problem**: `Error: Document is not valid OpenAPI`
**Solution**: Validate the spec at https://editor.swagger.io or run:
```bash
python backend/postman/validate_openapi.py
```

### CORS Errors in Browser

**Problem**: CORS errors when testing from frontend
**Solution**: Prism automatically handles CORS. Ensure you're using the correct URL (http://localhost:4010/api/v1)

### Unexpected Response Format

**Problem**: Response doesn't match expected structure
**Solution**: Check the OpenAPI spec examples. Prism returns the first example defined for each response.

## Next Steps

After successful Prism testing:

1. ✓ Verify all 27 endpoints return 200/201 status codes
2. ✓ Confirm response structures match OpenAPI schemas
3. ✓ Test with frontend application
4. ✓ Create Postman collection (Task 10)
5. ✓ Update README.md documentation (Task 15)

## Additional Resources

- Prism Documentation: https://meta.stoplight.io/docs/prism/
- OpenAPI Specification: https://swagger.io/specification/
- Swagger Editor: https://editor.swagger.io/
