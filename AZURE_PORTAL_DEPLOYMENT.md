# Deploy PixCrawler via Azure Portal (Website)

This guide shows you how to deploy using the Azure Portal website instead of CLI commands.

## 🌐 Method 1: Azure Portal (Visual Interface)

### Step 1: Create Azure Account
1. Go to: https://azure.microsoft.com/free/
2. Click "Start free"
3. Sign in with Microsoft account
4. Complete registration (credit card required but won't be charged)
5. Get $200 free credit

### Step 2: Access Azure Portal
1. Go to: https://portal.azure.com
2. Sign in with your Microsoft account
3. You'll see the Azure dashboard

### Step 3: Create a Web App

#### 3.1 Start Creation
1. Click **"Create a resource"** (top-left or center)
2. Search for **"Web App"**
3. Click **"Web App"** by Microsoft
4. Click **"Create"**

#### 3.2 Configure Basics Tab

**Project Details:**
- **Subscription:** Select your subscription (usually "Azure subscription 1")
- **Resource Group:** Click "Create new"
  - Name: `pixcrawler-rg`
  - Click "OK"

**Instance Details:**
- **Name:** `pixcrawler-test-YOUR-NAME-123` (must be globally unique)
  - Example: `pixcrawler-test-ahmed-456`
  - This will be your URL: `https://pixcrawler-test-ahmed-456.azurewebsites.net`
- **Publish:** Select **"Code"**
- **Runtime stack:** Select **"Python 3.10"**
- **Operating System:** Select **"Linux"**
- **Region:** Select **"East US"** (or closest to you)

**Pricing Plan:**
- Click **"Change size"**
- Click **"Dev / Test"** tab
- Select **"B1"** (Basic)
  - Shows: ~$13/month
  - Click **"Apply"**

#### 3.3 Review + Create
1. Click **"Review + create"** (bottom)
2. Wait for validation (green checkmark)
3. Click **"Create"**
4. Wait 2-3 minutes for deployment

#### 3.4 Go to Resource
1. When deployment completes, click **"Go to resource"**
2. You're now on your Web App page

### Step 4: Deploy Your Code

#### 4.1 Set Up Deployment Center
1. In the left menu, scroll down to **"Deployment"** section
2. Click **"Deployment Center"**
3. Under **"Source"**, select **"Local Git"**
4. Click **"Save"** (top)
5. Wait for it to configure

#### 4.2 Get Git Credentials
1. Still in Deployment Center
2. Click **"Local Git/FTPS credentials"** tab (top)
3. Under **"User Scope"**:
   - **Username:** Copy this (like `pixcrawler-test-ahmed-456\$pixcrawler-test-ahmed-456`)
   - **Password:** Click "Copy" icon
   - **Save these somewhere!**

#### 4.3 Get Git URL
1. Go back to **"Local Git"** tab
2. Copy the **"Git Clone Uri"**
   - Looks like: `https://pixcrawler-test-ahmed-456.scm.azurewebsites.net/pixcrawler-test-ahmed-456.git`

#### 4.4 Deploy via Git (PowerShell)
Open PowerShell in your project folder:

```powershell
# Navigate to your project
cd "f:\Projects\Languages\Python\WorkingOnIt\PixCrawler"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial deployment"

# Add Azure remote (replace with YOUR Git Clone Uri)
git remote add azure https://pixcrawler-test-ahmed-456.scm.azurewebsites.net/pixcrawler-test-ahmed-456.git

# Push to Azure (will ask for username/password)
git push azure master
```

When prompted:
- **Username:** Paste the username from step 4.2
- **Password:** Paste the password from step 4.2

Wait 5-10 minutes for deployment to complete.

### Step 5: Configure Startup Command

#### 5.1 Go to Configuration
1. In left menu, under **"Settings"**
2. Click **"Configuration"**
3. Click **"General settings"** tab

#### 5.2 Set Startup Command
1. Find **"Startup Command"** field
2. Enter: `startup.sh`
3. Click **"Save"** (top)
4. Click **"Continue"** when prompted
5. App will restart (takes 2-3 minutes)

### Step 6: Test Your Deployment

#### 6.1 Get Your URL
1. Go back to **"Overview"** (left menu, top)
2. Find **"Default domain"**
3. Copy the URL (like `https://pixcrawler-test-ahmed-456.azurewebsites.net`)

#### 6.2 Test Health Endpoint
Open in browser:
```
https://pixcrawler-test-ahmed-456.azurewebsites.net/health
```

Should see:
```json
{"status":"healthy"}
```

#### 6.3 View API Docs
Open in browser:
```
https://pixcrawler-test-ahmed-456.azurewebsites.net/docs
```

You'll see interactive API documentation!

#### 6.4 Run Automated Test
In PowerShell:
```powershell
.\test_azure_api.ps1 -AppName "pixcrawler-test-ahmed-456"
```

### Step 7: Monitor Your App

#### View Logs
1. In left menu, under **"Monitoring"**
2. Click **"Log stream"**
3. See real-time logs

#### Check Metrics
1. In left menu, under **"Monitoring"**
2. Click **"Metrics"**
3. See CPU, Memory, HTTP requests

### Step 8: Clean Up (When Done)

#### Stop the App (Keep for Later)
1. Go to **"Overview"**
2. Click **"Stop"** (top toolbar)
3. No charges while stopped

#### Delete Everything
1. Go to **"Overview"**
2. Click **"Delete"** (top toolbar)
3. Type the app name to confirm
4. Click **"Delete"**

Or delete the entire resource group:
1. In top search bar, search for **"Resource groups"**
2. Click **"Resource groups"**
3. Find **"pixcrawler-rg"**
4. Click on it
5. Click **"Delete resource group"** (top)
6. Type `pixcrawler-rg` to confirm
7. Click **"Delete"**

---

## 🌐 Method 2: Azure Portal with ZIP Deploy (Easier!)

This is even simpler - no Git needed!

### Step 1-3: Same as Above
Follow steps 1-3 from Method 1 to create the Web App.

### Step 4: Deploy via ZIP

#### 4.1 Create ZIP File
In PowerShell:
```powershell
cd "f:\Projects\Languages\Python\WorkingOnIt\PixCrawler"

# Create a ZIP of your project
Compress-Archive -Path * -DestinationPath pixcrawler-deploy.zip -Force
```

#### 4.2 Upload via Portal
1. In your Web App, go to **"Development Tools"** → **"Advanced Tools"**
2. Click **"Go"** (opens Kudu)
3. In Kudu, click **"Tools"** → **"Zip Push Deploy"**
4. Drag and drop your `pixcrawler-deploy.zip` file
5. Wait for upload and extraction

#### 4.3 Configure Startup
Follow Step 5 from Method 1 to set startup command.

---

## 🌐 Method 3: VS Code Extension (Easiest!)

If you use VS Code:

### Install Extension
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for **"Azure App Service"**
4. Install it
5. Sign in to Azure

### Deploy
1. Right-click your project folder
2. Select **"Deploy to Web App"**
3. Follow the prompts
4. Done!

---

## 🆘 Troubleshooting

### App Shows "Application Error"
- Wait 3-5 minutes after deployment
- Check logs in Log Stream
- Verify startup.sh is set in Configuration

### Can't Access /docs
- App may still be starting
- Check if /health works first
- Review logs for errors

### Deployment Takes Forever
- First deployment is slow (installing packages)
- 10-15 minutes is normal
- Check Deployment Center for progress

### "Name Already Taken"
- Someone else is using that name
- Try a different name with more random numbers
- Names must be globally unique

---

## 📊 Cost Tracking

### View Your Spending
1. In Azure Portal, search for **"Cost Management"**
2. Click **"Cost analysis"**
3. See your spending

### Set Budget Alert
1. In Cost Management, click **"Budgets"**
2. Click **"Add"**
3. Set budget (e.g., $10)
4. Set alert at 80%
5. Enter your email

---

## 🎯 Which Method Should You Use?

| Method | Difficulty | Best For |
|--------|-----------|----------|
| **Portal + Git** | Medium | Learning Git deployment |
| **Portal + ZIP** | Easy | Quick one-time test |
| **VS Code Extension** | Easiest | Regular deployments |
| **Azure CLI** | Advanced | Automation, scripts |

**Recommendation for first time:** Use **Portal + ZIP** (Method 2) - it's the simplest!

---

## 📚 Next Steps

After successful deployment:
1. Test both questions (image generation + URLs)
2. Check disk usage in SSH console
3. Review logs for any errors
4. Try with different image counts
5. Document your findings

**You don't need CLI at all!** The Portal is perfectly fine for testing. 🎉
