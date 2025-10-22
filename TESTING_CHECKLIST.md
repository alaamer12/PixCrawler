# Azure Deployment Testing Checklist

Use this checklist to systematically test your Azure deployment.

## ✅ Pre-Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] Azure CLI installed (`az --version`)
- [ ] Azure account with active subscription
- [ ] Git installed (for deployment)

## 📝 Local Testing (Do This First!)

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn pydantic
```
- [ ] Dependencies installed successfully

### Step 2: Start API Server
```bash
python api_main.py
```
- [ ] Server starts without errors
- [ ] Accessible at http://localhost:8000
- [ ] `/docs` endpoint shows Swagger UI

### Step 3: Run Automated Tests
```bash
python test_api_local.py
```
- [ ] Health check passes
- [ ] Dataset generation starts
- [ ] Job completes successfully
- [ ] Images are listed with URLs
- [ ] Images are accessible

**If all local tests pass, proceed to Azure deployment.**

## 🚀 Azure Deployment Checklist

### Step 1: Login to Azure
```bash
az login
```
- [ ] Successfully logged in
- [ ] Correct subscription selected

### Step 2: Deploy Application
```bash
az webapp up \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID \
  --runtime "PYTHON:3.10" \
  --sku B1
```
- [ ] Resource group created
- [ ] App Service plan created
- [ ] Web app created
- [ ] Code deployed
- [ ] Deployment URL received

### Step 3: Configure Startup
```bash
az webapp config set \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID \
  --startup-file "startup.sh"
```
- [ ] Startup command configured

### Step 4: Wait for Deployment
```bash
az webapp log tail \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID
```
- [ ] Application started successfully
- [ ] No errors in logs
- [ ] Gunicorn workers running

## 🧪 Azure Testing Checklist

### Test 1: Health Check
```bash
curl https://pixcrawler-test-YOUR-ID.azurewebsites.net/health
```
- [ ] Returns `{"status": "healthy"}`
- [ ] HTTP 200 status code

### Test 2: API Documentation
Visit: `https://pixcrawler-test-YOUR-ID.azurewebsites.net/docs`
- [ ] Swagger UI loads
- [ ] All endpoints visible
- [ ] Can interact with API

### Test 3: Start Generation Job
```bash
curl -X POST "https://pixcrawler-test-YOUR-ID.azurewebsites.net/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "azure_test",
    "categories": {"animals": ["cat"], "vehicles": ["car"]},
    "max_images": 5,
    "keyword_generation": "disabled"
  }'
```
- [ ] Returns job_id
- [ ] Status is "pending"
- [ ] Created timestamp present

### Test 4: Check Job Status
```bash
curl "https://pixcrawler-test-YOUR-ID.azurewebsites.net/api/status/JOB-ID"
```
- [ ] Status changes from "pending" to "running"
- [ ] Eventually becomes "completed"
- [ ] No errors reported
- [ ] Total images count present

### Test 5: List Generated Images
```bash
curl "https://pixcrawler-test-YOUR-ID.azurewebsites.net/api/images/JOB-ID"
```
- [ ] Returns list of images
- [ ] Each image has URL
- [ ] Each image has category
- [ ] Total count matches expectation

### Test 6: Access Individual Image
Visit: `https://pixcrawler-test-YOUR-ID.azurewebsites.net/images/JOB-ID/animals/000001.jpg`
- [ ] Image displays in browser
- [ ] Image downloads successfully
- [ ] Correct content-type header
- [ ] File size reasonable

## 🎯 Goal Verification

### ✅ Goal 1: Can Azure generate images locally on cloud?
- [ ] Images downloaded from search engines
- [ ] Images stored in datasets/ directory
- [ ] Integrity checks performed
- [ ] No Azure policy blocks

**Evidence:**
- Job status shows "completed"
- Total images count > 0
- No permission errors in logs

### ✅ Goal 2: Can you get URLs for each image?
- [ ] `/api/images/{job_id}` returns URLs
- [ ] URLs are accessible
- [ ] Images viewable in browser
- [ ] URLs follow pattern: `/images/{job_id}/{category}/{filename}`

**Evidence:**
- Image list endpoint works
- Individual image URLs work
- Can download images via URLs

## 📊 Performance Metrics

Record these for reference:

| Metric             | Value         |
|--------------------|---------------|
| Images requested   | _____         |
| Images downloaded  | _____         |
| Time to complete   | _____ seconds |
| Total dataset size | _____ MB      |
| Disk space used    | _____ MB      |
| Memory usage peak  | _____ MB      |

## 🐛 Troubleshooting

If tests fail, check:

### Application Won't Start
- [ ] Check logs: `az webapp log tail`
- [ ] Verify startup.sh is configured
- [ ] Check Python version in runtime.txt
- [ ] Verify all dependencies in requirements-azure.txt

### Job Stays Pending
- [ ] Check background task started
- [ ] Review application logs
- [ ] Verify PixCrawler dependencies installed
- [ ] Check for import errors

### Images Not Accessible
- [ ] Verify job status is "completed"
- [ ] Check datasets/ directory exists
- [ ] Verify file permissions
- [ ] Check path security validation

### Out of Disk Space
- [ ] Check disk usage in SSH session
- [ ] Reduce max_images parameter
- [ ] Clear old datasets
- [ ] Consider upgrading tier

## 🧹 Cleanup Checklist

After testing is complete:

### Option 1: Stop (Keep for Later)
```bash
az webapp stop \
  --resource-group pixcrawler-rg \
  --name pixcrawler-test-YOUR-ID
```
- [ ] App stopped (no charges while stopped)
- [ ] Can restart later

### Option 2: Delete Everything
```bash
az group delete --name pixcrawler-rg --yes
```
- [ ] Resource group deleted
- [ ] All resources removed
- [ ] No ongoing charges

## 📋 Test Results Summary

**Date:** _______________
**Tester:** _______________
**Azure Region:** _______________

### Results

| Test               | Pass/Fail | Notes |
|--------------------|-----------|-------|
| Local health check | ⬜         |       |
| Local generation   | ⬜         |       |
| Local image access | ⬜         |       |
| Azure deployment   | ⬜         |       |
| Azure health check | ⬜         |       |
| Azure generation   | ⬜         |       |
| Azure image URLs   | ⬜         |       |
| Azure image access | ⬜         |       |

### Final Verdict

**Question 1: Can Azure generate images locally?**
- [ ] YES ✅
- [ ] NO ❌
- [ ] PARTIAL ⚠️

**Question 2: Can you get URLs for images?**
- [ ] YES ✅
- [ ] NO ❌
- [ ] PARTIAL ⚠️

### Recommendations

Based on test results:

- [ ] Proceed with full implementation
- [ ] Need to address issues first
- [ ] Consider alternative approach

### Notes

_Add any additional observations or issues encountered:_

---

**Next Steps:**
1. If tests pass → Review README_API.md for production considerations
2. If tests fail → Check AZURE_DEPLOYMENT.md troubleshooting section
3. Document results → Share with team for decision making
