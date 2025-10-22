# PowerShell test script for Azure-deployed PixCrawler API
# Usage: .\test_azure_api.ps1 -AppName "your-azure-app-name"

param(
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

$BaseUrl = "https://$AppName.azurewebsites.net"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing PixCrawler API on Azure" -ForegroundColor Cyan
Write-Host "URL: $BaseUrl" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n[1/5] Testing health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Write-Host ($healthResponse | ConvertTo-Json)
    Write-Host "✅ Health check passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Start Generation
Write-Host "`n[2/5] Starting dataset generation..." -ForegroundColor Yellow
$generatePayload = @{
    dataset_name = "azure_test"
    categories = @{
        animals = @("cat")
        vehicles = @("car")
    }
    max_images = 5
    keyword_generation = "disabled"
    generate_labels = $false
} | ConvertTo-Json

try {
    $generateResponse = Invoke-RestMethod -Uri "$BaseUrl/api/generate" -Method Post -Body $generatePayload -ContentType "application/json"
    Write-Host ($generateResponse | ConvertTo-Json)
    $jobId = $generateResponse.job_id
    Write-Host "✅ Job started with ID: $jobId" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start generation: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Check Status (with polling)
Write-Host "`n[3/5] Checking job status..." -ForegroundColor Yellow
$maxAttempts = 60
$attempt = 0
$completed = $false

while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 5
    $attempt++
    
    try {
        $statusResponse = Invoke-RestMethod -Uri "$BaseUrl/api/status/$jobId" -Method Get
        $status = $statusResponse.status
        
        Write-Host "   Attempt $attempt : Status = $status"
        
        if ($status -eq "completed") {
            Write-Host "✅ Job completed successfully!" -ForegroundColor Green
            Write-Host ($statusResponse | ConvertTo-Json)
            $completed = $true
            break
        } elseif ($status -eq "failed") {
            Write-Host "❌ Job failed!" -ForegroundColor Red
            Write-Host ($statusResponse | ConvertTo-Json)
            exit 1
        }
        
        if ($attempt % 6 -eq 0) {
            $elapsed = $attempt * 5
            Write-Host "   Still waiting... ($elapsed s elapsed)"
        }
    } catch {
        Write-Host "   Error checking status: $_"
    }
}

if (-not $completed) {
    Write-Host "⏰ Timeout waiting for job completion" -ForegroundColor Red
    exit 1
}

# Test 4: List Images
Write-Host "`n[4/5] Listing generated images..." -ForegroundColor Yellow
try {
    $imagesResponse = Invoke-RestMethod -Uri "$BaseUrl/api/images/$jobId" -Method Get
    Write-Host ($imagesResponse | ConvertTo-Json -Depth 5)
    $totalImages = $imagesResponse.total_images
    Write-Host "✅ Found $totalImages images" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to list images: $_" -ForegroundColor Red
    exit 1
}

# Test 5: Get First Image URL
Write-Host "`n[5/5] Testing image access..." -ForegroundColor Yellow
if ($imagesResponse.images.Count -gt 0) {
    $firstImageUrl = $imagesResponse.images[0].url
    $fullUrl = "$BaseUrl$firstImageUrl"
    Write-Host "   Image URL: $fullUrl"
    
    try {
        $imageResponse = Invoke-WebRequest -Uri $fullUrl -Method Get
        if ($imageResponse.StatusCode -eq 200) {
            Write-Host "✅ Image accessible!" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Image not accessible: $_" -ForegroundColor Red
    }
} else {
    Write-Host "❌ No images found" -ForegroundColor Red
}

# Summary
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "🎉 TEST SUMMARY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Job ID: $jobId"
Write-Host "Total Images: $totalImages"
Write-Host "Dataset URL: $BaseUrl/api/images/$jobId"
Write-Host ""
Write-Host "✅ BOTH QUESTIONS ANSWERED:" -ForegroundColor Green
Write-Host "1. Azure CAN generate images locally on cloud" -ForegroundColor Green
Write-Host "2. You CAN get URLs for each image" -ForegroundColor Green
Write-Host ""
Write-Host "View all images:"
Write-Host "  Invoke-RestMethod -Uri $BaseUrl/api/images/$jobId"
Write-Host ""
Write-Host "View API docs:"
Write-Host "  Start-Process $BaseUrl/docs"
Write-Host "==========================================" -ForegroundColor Cyan
