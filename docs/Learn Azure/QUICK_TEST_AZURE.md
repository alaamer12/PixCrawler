# Quick Start: Azure Deployment Test

## 🎯 Goal
Test if PixCrawler can:
1. ✅ Generate and process images locally on Azure cloud
2. ✅ Provide URLs for each created image

## 🚀 Fastest Path to Test

### Step 1: Test Locally (5 minutes)
```bash
# Install FastAPI dependencies
pip install fastapi uvicorn pydantic

# Start the API
python api_main.py

# In another terminal, run tests
python test_api_local.py
```

### Step 2: Deploy to Azure (10 minutes)
```bash
# Login to Azure
az login

# Deploy in one command
az webapp up \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID \
  --runtime "PYTHON:3.11" \
  --sku B1

# Configure startup
az webapp config set \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID \
  --startup-file "startup.sh"
```

### Step 3: Test on Azure (2 minutes)
```bash
# Replace YOUR-ID with your app name
export AZURE_URL="https://pixcrawler-test-YOUR-ID.azurewebsites.net"

# Test health
curl $AZURE_URL/health

# Start generation
curl -X POST "$AZURE_URL/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "azure_test",
    "categories": {"animals": ["cat"], "vehicles": ["car"]},
    "max_images": 5,
    "keyword_generation": "disabled"
  }'

# Save the job_id from response, then check status
curl "$AZURE_URL/api/status/YOUR-JOB-ID"

# Once completed, get image URLs
curl "$AZURE_URL/api/images/YOUR-JOB-ID"

# Access an image in browser
# Open: https://pixcrawler-test-YOUR-ID.azurewebsites.net/images/YOUR-JOB-ID/animals/000001.jpg
```

## 📊 Expected Results

### Question 1: Can Azure generate images locally?
**YES** ✅
- Images download from search engines
- Processed in container filesystem
- Stored in `datasets/` directory
- All integrity checks work

**Note:** Storage is ephemeral (lost on restart). For production, use Azure Blob Storage.

### Question 2: Can you get URLs for images?
**YES** ✅
- Each image gets a unique URL: `/images/{job_id}/{category}/{filename}`
- Full URL: `https://your-app.azurewebsites.net/images/{job_id}/{category}/{filename}`
- Images served directly via FastAPI
- All images listed via `/api/images/{job_id}` endpoint

## 🔍 API Endpoints

| Endpoint                      | Purpose                  |
|-------------------------------|--------------------------|
| `POST /api/generate`          | Start dataset generation |
| `GET /api/status/{job_id}`    | Check progress           |
| `GET /api/images/{job_id}`    | List all image URLs      |
| `GET /images/{job_id}/{path}` | View/download image      |

## 📖 Full Documentation
See `AZURE_DEPLOYMENT.md` for complete details.

## 🧹 Cleanup
```bash
az group delete --name pixcrawler-rg --yes
```

## 💡 Tips
- Start with `max_images: 5` for quick tests
- Use `keyword_generation: "disabled"` to skip AI generation
- Check logs: `az webapp log tail --name pixcrawler-test-YOUR-ID --resource-group pixcrawler-rg`
- View API docs: `https://your-app.azurewebsites.net/docs`
