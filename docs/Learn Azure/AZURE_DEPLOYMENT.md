# Azure Deployment Guide for PixCrawler

This guide will help you deploy the minimal PixCrawler FastAPI application to Azure App Service to test:
1. ✅ Whether Azure can generate and process images locally on the cloud
2. ✅ Whether you can get URLs for each created image

## Prerequisites

- Azure account with active subscription
- Azure CLI installed (`az --version` to check)
- Git installed

## Quick Deployment Steps

### Option 1: Deploy via Azure CLI (Recommended)

#### 1. Login to Azure
```bash
az login
```

#### 2. Create a Resource Group
```bash
az group create --name pixcrawler-rg --location eastus
```

#### 3. Create an App Service Plan (Linux)
```bash
az appservice plan create \
  --name pixcrawler-plan \
  --resource-group pixcrawler-rg \
  --sku B1 \
  --is-linux
```

#### 4. Create the Web App
```bash
az webapp create \
  --resource-group pixcrawler-rg \
  --plan pixcrawler-plan \
  --name pixcrawler-test-<your-unique-id> \
  --runtime "PYTHON:3.11"
```
**Note:** Replace `<your-unique-id>` with something unique (e.g., your initials + random numbers)

#### 5. Configure Startup Command
```bash
az webapp config set \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-<your-unique-id> \
  --startup-file "startup.sh"
```

#### 6. Configure App Settings (Optional - for AI features)
```bash
az webapp config appsettings set \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-<your-unique-id> \
  --settings OPENAI_API_KEY="your-key-here"
```

#### 7. Deploy the Code
```bash
# From the PixCrawler directory
az webapp up \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-<your-unique-id> \
  --runtime "PYTHON:3.11"
```

### Option 2: Deploy via Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → "Web App"
3. Configure:
   - **Resource Group:** Create new "pixcrawler-rg"
   - **Name:** pixcrawler-test-<unique-id>
   - **Publish:** Code
   - **Runtime stack:** Python 3.11
   - **Operating System:** Linux
   - **Region:** East US (or your preferred region)
   - **Pricing Plan:** B1 (Basic)
4. Click "Review + Create" → "Create"
5. Once created, go to "Deployment Center"
6. Choose "Local Git" or "GitHub" and follow the instructions
7. In "Configuration" → "General settings", set:
   - **Startup Command:** `startup.sh`

## Testing the Deployment

### 1. Check Health Endpoint
Once deployed, your app will be available at:
```
https://pixcrawler-test-<your-unique-id>.azurewebsites.net
```

Test the health endpoint:
```bash
curl https://pixcrawler-test-<your-unique-id>.azurewebsites.net/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Test Dataset Generation (Answer Question #1)

**This tests if Azure can generate and process images locally on the cloud.**

Send a POST request to generate a small dataset:

```bash
curl -X POST "https://pixcrawler-test-<your-unique-id>.azurewebsites.net/api/generate" \
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
  }'
```

Expected response:
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Dataset generation started",
  "created_at": "2025-01-21T14:30:00"
}
```

**Save the `job_id` for the next steps!**

### 3. Check Generation Status

```bash
curl "https://pixcrawler-test-<your-unique-id>.azurewebsites.net/api/status/<job_id>"
```

Wait until status is "completed" (may take 1-3 minutes for 5 images).

### 4. Get Image URLs (Answer Question #2)

**This tests if you can get URLs for each created image.**

```bash
curl "https://pixcrawler-test-<your-unique-id>.azurewebsites.net/api/images/<job_id>"
```

Expected response:
```json
{
  "job_id": "abc-123-def-456",
  "dataset_name": "azure_test",
  "total_images": 10,
  "images": [
    {
      "filename": "000001.jpg",
      "category": "animals",
      "url": "/images/abc-123-def-456/animals/000001.jpg",
      "size_bytes": 45678
    },
    {
      "filename": "000002.jpg",
      "category": "animals",
      "url": "/images/abc-123-def-456/animals/000002.jpg",
      "size_bytes": 52341
    }
  ]
}
```

### 5. Access Individual Images

Open in browser or curl:
```bash
curl "https://pixcrawler-test-<your-unique-id>.azurewebsites.net/images/<job_id>/animals/000001.jpg" \
  --output test_image.jpg
```

## API Documentation

Once deployed, visit:
```
https://pixcrawler-test-<your-unique-id>.azurewebsites.net/docs
```

This provides interactive Swagger UI documentation for all endpoints.

## Available Endpoints

| Method | Endpoint                  | Description              |
|--------|---------------------------|--------------------------|
| GET    | `/`                       | Root endpoint            |
| GET    | `/health`                 | Health check             |
| POST   | `/api/generate`           | Start dataset generation |
| GET    | `/api/status/{job_id}`    | Check job status         |
| GET    | `/api/images/{job_id}`    | List all image URLs      |
| GET    | `/images/{job_id}/{path}` | Serve individual image   |
| GET    | `/api/jobs`               | List all jobs            |

## Expected Test Results

### ✅ Question 1: Will it generate and process images locally on the cloud?

**YES** - The Azure App Service will:
- Download images from search engines (Google, Bing, etc.)
- Process them locally in the container's filesystem
- Store them in the `datasets/` directory
- Perform integrity checks and deduplication

**Limitations to be aware of:**
- Azure App Service has ephemeral storage (files are lost on restart)
- For production, you'll need Azure Blob Storage for persistent storage
- Basic tier has ~1GB temporary storage limit

### ✅ Question 2: Will you be able to get URLs for each created image?

**YES** - The API provides:
- `/api/images/{job_id}` endpoint that lists all images with their URLs
- `/images/{job_id}/{path}` endpoint that serves the actual image files
- Each image gets a unique URL like: `/images/{job_id}/category/filename.jpg`

**For production:**
- Consider using Azure Blob Storage with SAS tokens for direct access
- Current implementation serves files through FastAPI (works but not optimal for scale)

## Monitoring & Debugging

### View Logs
```bash
az webapp log tail \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-<your-unique-id>
```

### SSH into Container (for debugging)
```bash
az webapp ssh \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-<your-unique-id>
```

### Check Disk Usage
Once SSH'd in:
```bash
df -h
ls -lah datasets/
```

## Troubleshooting

### Issue: App doesn't start
- Check logs: `az webapp log tail`
- Verify startup command is set to `startup.sh`
- Ensure all dependencies are in `requirements-azure.txt`

### Issue: Out of disk space
- Azure Basic tier has limited storage (~1GB)
- Reduce `max_images` in test requests
- Consider upgrading to Standard tier or using Blob Storage

### Issue: Slow image generation
- This is expected - downloading images takes time
- Azure policies don't block image downloads
- Network speed depends on Azure region and source websites

### Issue: Job status shows "failed"
- Check the error message in `/api/status/{job_id}`
- Common issues:
  - Network timeouts (increase timeout in startup.sh)
  - Missing dependencies
  - Rate limiting from search engines

## Clean Up Resources

When done testing:
```bash
az group delete --name pixcrawler-rg --yes --no-wait
```

## Next Steps for Production

If tests are successful, consider:

1. **Persistent Storage:**
   - Integrate Azure Blob Storage for image persistence
   - Use Azure Storage SDK to upload images
   - Generate SAS URLs for direct image access

2. **Scalability:**
   - Use Azure Functions or Container Apps for better scaling
   - Implement Redis for job queue management
   - Use Azure Service Bus for async processing

3. **Security:**
   - Add authentication (Azure AD, API keys)
   - Implement rate limiting
   - Use Azure Key Vault for secrets

4. **Monitoring:**
   - Enable Application Insights
   - Set up alerts for failures
   - Track performance metrics

## Cost Estimation

For testing (B1 Basic tier):
- ~$13-15/month if kept running
- Can stop/start the app to save costs
- Free tier available but very limited (60 min/day CPU time)

## Support

If you encounter issues:
1. Check Azure logs: `az webapp log tail`
2. Review the `/api/jobs` endpoint for job details
3. Test locally first: `python api_main.py`
