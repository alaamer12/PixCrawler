# AI Prompt: Complete PixCrawler Postman Mock Collections

## Objective

Add all missing backend API endpoints to the Postman mock collection (`PixCrawler_Frontend_Mock.json`) and OpenAPI specification (`openapi.json`) to enable complete frontend development without running the Python backend. **All responses must be success cases (200/201 status codes)** with realistic mock data.

## Current Status

### ✅ Already Implemented in Mock Collection
- **Auth**: `/auth/me`, `/auth/verify-token`, `/auth/sync-profile`
- **Projects**: Full CRUD (List, Get, Create, Update, Delete)
- **Datasets**: List (by project), Get, Create, Stats, Build, Status
- **Jobs**: List, Get Logs
- **Notifications**: List, Mark as Read, Mark All Read

### ❌ Missing Endpoints (Verified from Backend)

Based on analysis of `backend/api/v1/router.py` and endpoint files, the following are **actually implemented** in the backend but missing from the mock:

---

## Priority 1: Crawl Jobs (HIGH PRIORITY) ⭐

**File**: `backend/api/v1/endpoints/crawl_jobs.py`  
**Prefix**: `/jobs`

### Missing Endpoints:

1. **POST /jobs/** - Create crawl job
   - Status: 201 Created
   - Request Body:
   ```json
   {
     "project_id": 1,
     "name": "Cat Images Dataset",
     "keywords": ["cats", "kittens", "felines"],
     "max_images": 1000
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "id": 1,
       "project_id": 1,
       "name": "Cat Images Dataset",
       "keywords": {"keywords": ["cats", "kittens", "felines"]},
       "max_images": 1000,
       "status": "pending",
       "progress": 0,
       "total_images": 0,
       "downloaded_images": 0,
       "valid_images": 0,
       "total_chunks": 0,
       "active_chunks": 0,
       "completed_chunks": 0,
       "failed_chunks": 0,
       "created_at": "2024-12-05T10:00:00Z",
       "updated_at": "2024-12-05T10:00:00Z",
       "started_at": null,
       "completed_at": null
     }
   }
   ```

2. **GET /jobs/{job_id}** - Get specific crawl job
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "id": 1,
       "project_id": 1,
       "name": "Cat Images Dataset",
       "keywords": {"keywords": ["cats", "kittens"]},
       "max_images": 1000,
       "status": "running",
       "progress": 65,
       "total_images": 650,
       "downloaded_images": 650,
       "valid_images": 620,
       "total_chunks": 6,
       "active_chunks": 2,
       "completed_chunks": 4,
       "failed_chunks": 0,
       "created_at": "2024-12-05T10:00:00Z",
       "updated_at": "2024-12-05T10:30:00Z",
       "started_at": "2024-12-05T10:05:00Z",
       "completed_at": null
     }
   }
   ```

3. **POST /jobs/{job_id}/start** - Start crawl job ⭐
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "job_id": 1,
       "status": "running",
       "task_ids": ["task_1_google_cats", "task_1_bing_cats", "task_1_duckduckgo_cats"],
       "total_chunks": 6,
       "message": "Job started successfully with 6 tasks"
     }
   }
   ```

4. **POST /jobs/{job_id}/cancel** - Cancel crawl job ⭐
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "job_id": 1,
       "status": "cancelled",
       "revoked_tasks": 3,
       "message": "Job cancelled successfully. 3 task(s) revoked."
     }
   }
   ```

5. **POST /jobs/{job_id}/retry** - Retry failed job
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "id": 1,
       "project_id": 1,
       "name": "Cat Images Dataset",
       "status": "pending",
       "progress": 0,
       "total_images": 0,
       "downloaded_images": 0,
       "valid_images": 0,
       "total_chunks": 0,
       "active_chunks": 0,
       "completed_chunks": 0,
       "failed_chunks": 0,
       "created_at": "2024-12-05T10:00:00Z",
       "updated_at": "2024-12-05T11:00:00Z",
       "started_at": null,
       "completed_at": null
     }
   }
   ```

6. **GET /jobs/{job_id}/progress** - Get job progress ⭐
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "job_id": 1,
       "status": "running",
       "progress": 75,
       "total_chunks": 10,
       "active_chunks": 2,
       "completed_chunks": 7,
       "failed_chunks": 1,
       "downloaded_images": 750,
       "estimated_completion": null,
       "started_at": "2024-12-05T10:05:00Z",
       "updated_at": "2024-12-05T10:20:00Z"
     }
   }
   ```

---

## Priority 2: Validation (HIGH PRIORITY) ⭐

**File**: `backend/api/v1/endpoints/validation.py`  
**Prefix**: `/validation`

### Missing Endpoints:

1. **POST /validation/analyze/** - Analyze single image
   - Status: 200 OK
   - Request Body:
   ```json
   {
     "image_url": "https://example.com/image.jpg"
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "is_valid": true,
       "is_duplicate": false,
       "validation_score": 0.95,
       "dimensions": {"width": 1920, "height": 1080},
       "file_size": 245678,
       "format": "jpeg"
     }
   }
   ```

2. **POST /validation/batch/** - Create batch validation
   - Status: 201 Created
   - Request Body:
   ```json
   {
     "image_ids": [1, 2, 3, 4, 5],
     "level": "medium"
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "batch_id": "batch_123",
       "status": "processing",
       "total_images": 5,
       "message": "Batch validation started"
     }
   }
   ```

3. **POST /validation/job/{job_id}/** - Validate job images ⭐
   - Status: 200 OK
   - Request Body:
   ```json
   {
     "level": "medium"
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "job_id": 1,
       "images_count": 100,
       "validation_level": "medium",
       "task_ids": ["val_task_1", "val_task_2"],
       "message": "Validation started for 100 images"
     }
   }
   ```

4. **GET /validation/results/{job_id}/** - Get validation results
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "job_id": 1,
       "total_images": 100,
       "valid_images": 95,
       "invalid_images": 3,
       "duplicate_images": 2,
       "validation_rate": 95.0,
       "completed_at": "2024-12-05T10:30:00Z"
     }
   }
   ```

5. **GET /validation/stats/{dataset_id}/** - Get dataset validation stats
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "dataset_id": 1,
       "total_images": 1000,
       "validated_images": 950,
       "valid_images": 920,
       "invalid_images": 30,
       "duplicate_images": 50,
       "validation_coverage": 95.0
     }
   }
   ```

6. **PUT /validation/level/** - Update validation level
   - Status: 200 OK
   - Request Body:
   ```json
   {
     "job_id": 1,
     "level": "strict"
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "job_id": 1,
       "validation_level": "strict",
       "message": "Validation level updated successfully"
     }
   }
   ```

---

## Priority 3: Credits & Billing (MEDIUM PRIORITY)

**File**: `backend/api/v1/endpoints/credits.py`  
**Prefix**: `/credits`

### Missing Endpoints:

1. **GET /credits/balance** - Get credit balance
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "user_id": "user_123",
       "current_balance": 1000,
       "monthly_usage": 250,
       "average_daily_usage": 8.33,
       "monthly_limit": 5000,
       "auto_refill_enabled": true,
       "refill_threshold": 100,
       "refill_amount": 500
     }
   }
   ```

2. **GET /credits/transactions** - List credit transactions
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": [
       {
         "id": 1,
         "type": "purchase",
         "amount": 1000,
         "balance_after": 1000,
         "status": "completed",
         "description": "Credit purchase",
         "created_at": "2024-12-01T10:00:00Z"
       },
       {
         "id": 2,
         "type": "usage",
         "amount": -50,
         "balance_after": 950,
         "status": "completed",
         "description": "Image processing",
         "created_at": "2024-12-02T14:30:00Z"
       }
     ],
     "meta": {
       "total": 2,
       "page": 1,
       "limit": 50
     }
   }
   ```

3. **POST /credits/purchase** - Purchase credits
   - Status: 201 Created
   - Request Body:
   ```json
   {
     "amount": 1000,
     "payment_method": "lemonsqueezy",
     "payment_token": "order_abc123"
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "transaction_id": 3,
       "type": "purchase",
       "amount": 1000,
       "balance_after": 2000,
       "status": "completed",
       "created_at": "2024-12-05T10:00:00Z"
     }
   }
   ```

4. **GET /credits/usage** - Get usage metrics
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "daily_usage": [
         {"date": "2024-12-01", "images_processed": 100, "credits_used": 10},
         {"date": "2024-12-02", "images_processed": 150, "credits_used": 15},
         {"date": "2024-12-03", "images_processed": 200, "credits_used": 20}
       ],
       "total_images_processed": 450,
       "total_credits_used": 45,
       "period": "last_7_days"
     }
   }
   ```

---

## Priority 4: API Keys (MEDIUM PRIORITY)

**File**: `backend/api/v1/endpoints/api_keys.py`  
**Prefix**: `/api-keys`

### Missing Endpoints:

1. **GET /api-keys/** - List API keys
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": [
       {
         "id": 1,
         "name": "Production API Key",
         "key_prefix": "pk_live_",
         "permissions": ["read", "write"],
         "rate_limit": 1000,
         "usage_count": 450,
         "last_used_at": "2024-12-05T09:30:00Z",
         "created_at": "2024-11-01T10:00:00Z",
         "expires_at": "2025-11-01T10:00:00Z",
         "status": "active"
       }
     ],
     "meta": {
       "total": 1
     }
   }
   ```

2. **POST /api-keys/** - Create API key
   - Status: 201 Created
   - Request Body:
   ```json
   {
     "name": "Development API Key",
     "permissions": ["read"],
     "rate_limit": 500,
     "expires_at": "2025-12-31T23:59:59Z"
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "id": 2,
       "name": "Development API Key",
       "key": "pk_test_1234567890abcdef1234567890abcdef",
       "key_prefix": "pk_test_",
       "permissions": ["read"],
       "rate_limit": 500,
       "created_at": "2024-12-05T10:00:00Z",
       "expires_at": "2025-12-31T23:59:59Z",
       "message": "API key created successfully. Store it securely - it won't be shown again."
     }
   }
   ```

3. **DELETE /api-keys/{key_id}** - Revoke API key
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "id": 2,
       "status": "revoked",
       "message": "API key revoked successfully"
     }
   }
   ```

4. **GET /api-keys/{key_id}/usage** - Get API key usage
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "key_id": 1,
       "usage_count": 450,
       "rate_limit": 1000,
       "remaining": 550,
       "last_used_at": "2024-12-05T09:30:00Z",
       "usage_by_day": [
         {"date": "2024-12-01", "requests": 100},
         {"date": "2024-12-02", "requests": 150},
         {"date": "2024-12-03", "requests": 200}
       ]
     }
   }
   ```

---

## Priority 5: Storage (MEDIUM PRIORITY)

**File**: `backend/api/v1/endpoints/storage.py`  
**Prefix**: `/storage`

### Missing Endpoints:

1. **GET /storage/usage/** - Get storage usage
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "user_id": "user_123",
       "total_storage_gb": 2.5,
       "storage_limit_gb": 100.0,
       "usage_percentage": 2.5,
       "files_count": 1250,
       "hot_storage_gb": 1.8,
       "warm_storage_gb": 0.7
     }
   }
   ```

2. **GET /storage/files/** - List storage files
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": [
       {
         "filename": "job_1_cats.zip",
         "size_bytes": 52428800,
         "size_mb": 50.0,
         "tier": "hot",
         "created_at": "2024-12-05T10:00:00Z",
         "download_url": "https://storage.example.com/job_1_cats.zip?token=abc123"
       },
       {
         "filename": "job_2_dogs.7z",
         "size_bytes": 31457280,
         "size_mb": 30.0,
         "tier": "warm",
         "created_at": "2024-12-04T15:00:00Z",
         "download_url": "https://storage.example.com/job_2_dogs.7z?token=def456"
       }
     ]
   }
   ```

3. **POST /storage/cleanup/** - Cleanup old files
   - Status: 200 OK
   - Request Body:
   ```json
   {
     "older_than_days": 30
   }
   ```
   - Response:
   ```json
   {
     "data": {
       "deleted_files": 15,
       "freed_space_gb": 5.2,
       "message": "Cleanup completed successfully"
     }
   }
   ```

4. **GET /storage/presigned-url/** - Generate presigned URL
   - Status: 200 OK
   - Query Params: `?file_path=job_1_cats.zip`
   - Response:
   ```json
   {
     "data": {
       "url": "https://storage.example.com/job_1_cats.zip?token=xyz789&expires=1733500000",
       "expires_at": "2024-12-05T12:00:00Z",
       "expires_in_seconds": 3600
     }
   }
   ```

---

## Priority 6: Activity Logs (LOW PRIORITY)

**File**: `backend/api/v1/endpoints/activity.py`  
**Prefix**: `/activity`

### Missing Endpoints:

1. **GET /activity/** - List activity logs
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": [
       {
         "id": 1,
         "user_id": "user_123",
         "action": "create",
         "resource_type": "crawl_job",
         "resource_id": "1",
         "metadata": {
           "keywords": ["cats", "dogs"],
           "max_images": 1000
         },
         "ip_address": "192.168.1.1",
         "user_agent": "Mozilla/5.0...",
         "timestamp": "2024-12-05T10:00:00Z"
       },
       {
         "id": 2,
         "user_id": "user_123",
         "action": "start",
         "resource_type": "crawl_job",
         "resource_id": "1",
         "metadata": {
           "task_ids": ["task_1", "task_2"]
         },
         "ip_address": "192.168.1.1",
         "user_agent": "Mozilla/5.0...",
         "timestamp": "2024-12-05T10:05:00Z"
       }
     ],
     "meta": {
       "total": 2,
       "page": 1,
       "limit": 50
     }
   }
   ```

---

## Priority 7: Health & System (LOW PRIORITY)

**File**: `backend/api/v1/endpoints/health.py`  
**Prefix**: `/health`

### Missing Endpoints:

1. **GET /health/** - Basic health check
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "status": "healthy",
       "timestamp": "2024-12-05T10:00:00Z",
       "version": "1.0.0"
     }
   }
   ```

2. **GET /health/detailed** - Detailed health check
   - Status: 200 OK
   - Response:
   ```json
   {
     "data": {
       "status": "healthy",
       "timestamp": "2024-12-05T10:00:00Z",
       "services": {
         "database": {
           "status": "healthy",
           "response_time_ms": 15,
           "message": "Database connection successful"
         },
         "redis": {
           "status": "healthy",
           "response_time_ms": 5,
           "message": "Redis connection successful"
         },
         "celery": {
           "status": "healthy",
           "workers": 2,
           "message": "2 worker(s) active"
         }
       },
       "uptime_seconds": 864000
     }
   }
   ```

---

## Implementation Instructions

### Step 1: Update Postman Collection JSON

For each missing endpoint, add to `frontend/postman/PixCrawler_Frontend_Mock.json`:

```json
{
  "name": "Endpoint Name",
  "request": {
    "method": "GET|POST|PATCH|DELETE|PUT",
    "header": [
      {
        "key": "Content-Type",
        "value": "application/json"
      }
    ],
    "body": {
      "mode": "raw",
      "raw": "{\n  \"key\": \"value\"\n}"
    },
    "url": {
      "raw": "{{baseUrl}}/path/to/endpoint",
      "host": ["{{baseUrl}}"],
      "path": ["path", "to", "endpoint"]
    }
  },
  "response": [
    {
      "name": "Success",
      "status": "OK",
      "code": 200,
      "_postman_previewlanguage": "json",
      "header": [
        {
          "key": "Content-Type",
          "value": "application/json"
        }
      ],
      "body": "{\n  \"data\": {}\n}"
    }
  ]
}
```

### Step 2: Update OpenAPI Specification

Add corresponding paths to `frontend/postman/openapi.json`:

```json
"/path/to/endpoint": {
  "get": {
    "summary": "Endpoint Name",
    "responses": {
      "200": {
        "description": "Success",
        "content": {
          "application/json": {
            "example": {
              "data": {}
            }
          }
        }
      }
    }
  }
}
```

### Step 3: Organize by Groups

In the Postman collection, organize endpoints into these groups:
- Auth (existing)
- Projects (existing)
- Datasets (existing)
- **Crawl Jobs** (add missing endpoints)
- **Validation** (new group)
- **Credits** (new group)
- **API Keys** (new group)
- **Storage** (new group)
- **Activity** (new group)
- **Health** (new group)
- Notifications (existing)

### Step 4: Test with Prism

```bash
cd frontend
prism mock postman/openapi.json -p 4010
```

Test each endpoint:
```bash
curl http://localhost:4010/api/v1/jobs/
curl http://localhost:4010/api/v1/validation/job/1/
curl http://localhost:4010/api/v1/credits/balance
curl http://localhost:4010/api/v1/health/
```

### Step 5: Update README

Update `frontend/postman/README.md` with:
- New endpoint groups
- Usage examples
- Any special notes

---

## Success Criteria

- [ ] All 35+ missing endpoints added to Postman collection
- [ ] All endpoints added to OpenAPI spec
- [ ] All responses return 200/201 status codes
- [ ] Mock data is realistic and matches backend schemas
- [ ] Prism mock server runs without errors
- [ ] All endpoints testable via curl/Postman
- [ ] README.md updated with new endpoints
- [ ] Frontend can use mock server for complete development

---

## Notes

- **All responses must be success cases** - no 400/404/500 errors
- Use realistic mock data that matches production schemas
- Follow existing naming conventions in the collection
- Ensure `{{baseUrl}}` variable is used for all URLs
- Add proper Content-Type headers
- Include pagination metadata where applicable
- Use ISO 8601 format for timestamps
- Follow the response structure: `{"data": {...}}` or `{"data": [...], "meta": {...}}`

---

## Estimated Time

- **Crawl Jobs**: 1.5 hours (7 endpoints)
- **Validation**: 1 hour (6 endpoints)
- **Credits**: 1 hour (4 endpoints)
- **API Keys**: 1 hour (4 endpoints)
- **Storage**: 1 hour (4 endpoints)
- **Activity**: 30 minutes (1 endpoint)
- **Health**: 30 minutes (2 endpoints)
- **Testing & Documentation**: 1 hour

**Total**: ~7.5 hours

---

## Priority Summary

1. **HIGH**: Crawl Jobs (7 endpoints) - Core functionality
2. **HIGH**: Validation (6 endpoints) - Core functionality
3. **MEDIUM**: Credits (4 endpoints) - User management
4. **MEDIUM**: API Keys (4 endpoints) - Programmatic access
5. **MEDIUM**: Storage (4 endpoints) - File management
6. **LOW**: Activity (1 endpoint) - Monitoring
7. **LOW**: Health (2 endpoints) - Diagnostics

**Total Missing Endpoints**: 28 endpoints
