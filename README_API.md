# PixCrawler FastAPI - Azure Deployment Test

This directory contains a minimal FastAPI application to test Azure deployment capabilities for PixCrawler.

## 📁 Files Overview

### Core API Files
- **`api_main.py`** - Main FastAPI application with all endpoints
- **`requirements-azure.txt`** - Python dependencies for Azure deployment
- **`startup.sh`** - Azure App Service startup script
- **`runtime.txt`** - Python version specification for Azure

### Testing Files
- **`test_api_local.py`** - Automated local testing script (Python)
- **`test_azure_api.ps1`** - Azure deployment testing script (PowerShell)
- **`test_azure_api.sh`** - Azure deployment testing script (Bash)

### Documentation
- **`AZURE_DEPLOYMENT.md`** - Complete deployment guide with troubleshooting
- **`QUICK_START_AZURE.md`** - Quick reference for fast deployment
- **`README_API.md`** - This file

### Configuration
- **`.deployment`** - Azure deployment configuration
- **`azure-deploy.yml`** - GitHub Actions workflow (optional)

## 🎯 Testing Goals

This setup answers two critical questions:

### ✅ Question 1: Can Azure generate images locally on the cloud?
**Answer: YES**
- Images are downloaded from search engines (Google, Bing, etc.)
- Processed locally in the Azure container's filesystem
- Stored in the `datasets/` directory
- All integrity checks and deduplication work normally

**Important Notes:**
- Azure App Service uses ephemeral storage (files lost on restart)
- Basic tier has ~1GB temporary storage limit
- For production, integrate Azure Blob Storage for persistence

### ✅ Question 2: Can you get URLs for each created image?
**Answer: YES**
- Each image gets a unique URL: `/images/{job_id}/{category}/{filename}`
- Full URL format: `https://your-app.azurewebsites.net/images/{job_id}/{category}/{filename}`
- Images are served directly via FastAPI FileResponse
- All images can be listed via `/api/images/{job_id}` endpoint

**Production Considerations:**
- Current implementation serves files through FastAPI (works but not optimal at scale)
- For production, use Azure Blob Storage with SAS tokens for direct access
- Consider CDN for better performance

## 🚀 Quick Start

### 1. Test Locally (Recommended First Step)
```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Start the API server
python api_main.py

# In another terminal, run automated tests
python test_api_local.py
```

The API will be available at `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 2. Deploy to Azure
```bash
# Login to Azure
az login

# Deploy (replace YOUR-ID with something unique)
az webapp up \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID \
  --runtime "PYTHON:3.10" \
  --sku B1

# Configure startup command
az webapp config set \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID \
  --startup-file "startup.sh"
```

### 3. Test Azure Deployment
```powershell
# PowerShell
.\test_azure_api.ps1 -AppName "pixcrawler-test-YOUR-ID"
```

```bash
# Bash
./test_azure_api.sh pixcrawler-test-YOUR-ID
```

## 📡 API Endpoints

| Method | Endpoint                  | Description                   |
|--------|---------------------------|-------------------------------|
| GET    | `/`                       | Root endpoint (health info)   |
| GET    | `/health`                 | Health check for monitoring   |
| POST   | `/api/generate`           | Start dataset generation job  |
| GET    | `/api/status/{job_id}`    | Check job status and progress |
| GET    | `/api/images/{job_id}`    | List all generated image URLs |
| GET    | `/images/{job_id}/{path}` | Serve individual image file   |
| GET    | `/api/jobs`               | List all jobs                 |
| GET    | `/docs`                   | Interactive API documentation |

## 💡 Usage Example

### Start a Generation Job
```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "test_dataset",
    "categories": {
      "animals": ["cat", "dog"],
      "vehicles": ["car"]
    },
    "max_images": 10,
    "keyword_generation": "disabled",
    "generate_labels": false
  }'
```

Response:
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Dataset generation started",
  "created_at": "2025-01-21T14:30:00"
}
```

### Check Job Status
```bash
curl "http://localhost:8000/api/status/abc-123-def-456"
```

### Get Image URLs
```bash
curl "http://localhost:8000/api/images/abc-123-def-456"
```

Response:
```json
{
  "job_id": "abc-123-def-456",
  "dataset_name": "test_dataset",
  "total_images": 20,
  "images": [
    {
      "filename": "000001.jpg",
      "category": "animals",
      "url": "/images/abc-123-def-456/animals/000001.jpg",
      "size_bytes": 45678
    }
  ]
}
```

### Access Image
Open in browser or download:
```
http://localhost:8000/images/abc-123-def-456/animals/000001.jpg
```

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────┐
│      FastAPI Application        │
│  ┌───────────────────────────┐  │
│  │  POST /api/generate       │  │
│  │  ├─ Create job_id         │  │
│  │  ├─ Start background task │  │
│  │  └─ Return job_id         │  │
│  └───────────────────────────┘  │
│                                  │
│  ┌───────────────────────────┐  │
│  │  Background Task          │  │
│  │  ├─ Load config           │  │
│  │  ├─ Generate dataset      │  │
│  │  ├─ Download images       │  │
│  │  └─ Update job status     │  │
│  └───────────────────────────┘  │
│                                  │
│  ┌───────────────────────────┐  │
│  │  GET /api/images/{job_id} │  │
│  │  ├─ Read dataset dir      │  │
│  │  ├─ Generate URLs         │  │
│  │  └─ Return image list     │  │
│  └───────────────────────────┘  │
│                                  │
│  ┌───────────────────────────┐  │
│  │  GET /images/{job_id}/... │  │
│  │  ├─ Validate path         │  │
│  │  ├─ Read image file       │  │
│  │  └─ Return FileResponse   │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Local Filesystem (datasets/)  │
│  ┌──────────────────────────┐   │
│  │ datasets/                │   │
│  │  └─ {job_id}_{name}/     │   │
│  │      ├─ animals/         │   │
│  │      │   ├─ 000001.jpg   │   │
│  │      │   └─ 000002.jpg   │   │
│  │      └─ vehicles/        │   │
│  │          └─ 000001.jpg   │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

## 🔧 Configuration

### Request Parameters
- **`dataset_name`** (required): Name for the dataset
- **`categories`** (required): Dict of category → keywords
- **`max_images`** (default: 10): Images per keyword (1-100)
- **`keyword_generation`** (default: "auto"): "auto", "enabled", or "disabled"
- **`ai_model`** (default: "gpt4-mini"): "gpt4" or "gpt4-mini"
- **`generate_labels`** (default: false): Generate ML label files

### Environment Variables (Optional)
- `OPENAI_API_KEY`: For AI-powered keyword generation
- `PORT`: Server port (default: 8000)

## 📊 Monitoring

### View Logs (Azure)
```bash
az webapp log tail \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID
```

### Check Disk Usage (Azure SSH)
```bash
az webapp ssh \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID

# Then in the SSH session:
df -h
du -sh datasets/*
```

## 🧹 Cleanup

### Stop Azure App (keep resources)
```bash
az webapp stop \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID
```

### Delete Everything
```bash
az group delete --name pixcrawler-rg --yes --no-wait
```

## 🐛 Troubleshooting

### API doesn't start locally
- Check if port 8000 is available
- Install dependencies: `pip install -r requirements-azure.txt`
- Check Python version: `python --version` (need 3.8+)

### Job stays in "pending" status
- Background task may have failed
- Check logs for errors
- Verify all PixCrawler dependencies are installed

### Images not accessible
- Ensure job status is "completed"
- Check if files exist in datasets directory
- Verify path security (must be within output directory)

### Azure deployment fails
- Check logs: `az webapp log tail`
- Verify startup.sh is executable
- Ensure requirements-azure.txt is complete
- Check Python version matches runtime.txt

## 📚 Additional Resources

- **Full Deployment Guide**: See `AZURE_DEPLOYMENT.md`
- **Quick Reference**: See `QUICK_START_AZURE.md`
- **API Documentation**: Visit `/docs` endpoint when running
- **Azure CLI Docs**: https://docs.microsoft.com/cli/azure/

## 💰 Cost Estimation

**Azure App Service B1 (Basic) Tier:**
- ~$13-15 USD/month if running continuously
- Can stop/start to save costs when not testing
- Free tier available but very limited (60 min/day CPU)

**Recommended for Testing:**
- Deploy → Test → Delete within same day = minimal cost
- Or use stop/start between test sessions

## 🔐 Security Notes

**Current Implementation (Test Only):**
- ⚠️ No authentication required
- ⚠️ In-memory job storage (lost on restart)
- ⚠️ No rate limiting
- ⚠️ Public access to all endpoints

**For Production, Add:**
- API key authentication or Azure AD
- Redis/Database for job persistence
- Rate limiting middleware
- Input validation and sanitization
- Azure Key Vault for secrets
- Private networking/VNet integration

## 🚀 Next Steps After Successful Test

If both tests pass (local generation + URL access):

1. **Add Persistent Storage**
   - Integrate Azure Blob Storage
   - Upload images to blob containers
   - Generate SAS URLs for direct access

2. **Improve Scalability**
   - Move to Azure Container Apps or Functions
   - Add Redis for job queue
   - Implement proper task queue (Celery)

3. **Production Hardening**
   - Add authentication
   - Implement rate limiting
   - Set up monitoring (Application Insights)
   - Add error tracking (Sentry)

4. **Optimize Performance**
   - Use CDN for image delivery
   - Implement caching
   - Optimize image processing pipeline

## 📞 Support

For issues or questions:
1. Check `AZURE_DEPLOYMENT.md` troubleshooting section
2. Review Azure logs
3. Test locally first to isolate Azure-specific issues
4. Check PixCrawler main documentation

---

**Ready to test?** Start with `python test_api_local.py` then deploy to Azure! 🚀
