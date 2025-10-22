# Azure Deployment for Complete Beginners 👶

**Welcome!** This guide assumes you've never used Azure before. We'll go step-by-step with screenshots descriptions and explanations.

## 🎯 What We're Going to Do

1. Create a free Azure account (if you don't have one)
2. Install a simple tool (Azure CLI) on your computer
3. Run a few commands to deploy your app
4. Test if it works
5. Delete everything when done (so you don't get charged)

**Time needed:** About 30 minutes for your first time

---

## Step 1: Create Azure Account (10 minutes)

### What is Azure?
Azure is Microsoft's cloud platform. Think of it like renting a computer from Microsoft that's always online.

### Create Your Account

1. **Go to:** https://azure.microsoft.com/free/
2. **Click:** "Start free" (green button)
3. **Sign in** with your Microsoft account (or create one)
4. **Fill in your details:**
   - Name, email, phone number
   - Credit card (required but you won't be charged during free trial)
5. **Get $200 free credit** for 30 days

**Important:** You get $200 FREE to test with. We'll use less than $1 for this test.

---

## Step 2: Install Azure CLI (5 minutes)

### What is Azure CLI?
It's a simple program that lets you control Azure from your command line (like PowerShell or Terminal).

### Installation

**For Windows (PowerShell):**
```powershell
# Open PowerShell as Administrator (right-click → Run as Administrator)
# Then run this command:
Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi
Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'
rm .\AzureCLI.msi
```

**Or download installer:**
- Go to: https://aka.ms/installazurecliwindows
- Download and run the installer
- Click "Next" a bunch of times
- Restart PowerShell when done

**Verify it worked:**
```powershell
az --version
```
You should see version information (not an error).

---

## Step 3: Login to Azure (2 minutes)

### Connect Your Computer to Your Azure Account

Open PowerShell (doesn't need to be Administrator) and run:

```powershell
az login
```

**What happens:**
1. A browser window opens
2. Sign in with your Microsoft account
3. Browser says "You're logged in"
4. Close the browser
5. PowerShell shows your subscription info

**Example output:**
```json
[
  {
    "name": "Azure subscription 1",
    "id": "abc-123-def-456",
    "isDefault": true
  }
]
```

✅ **You're now connected!**

---

## Step 4: Deploy Your App (10 minutes)

### What We're Doing
We're going to:
1. Create a "resource group" (think: a folder to organize things)
2. Create an "app service" (think: a computer to run your code)
3. Upload your code to that computer

### The Commands

**Open PowerShell** and navigate to your project:
```powershell
cd "f:\Projects\Languages\Python\WorkingOnIt\PixCrawler"
```

**Run this ONE command** (replace `YOUR-NAME-123` with your name + random numbers):
```powershell
az webapp up `
  --resource-group pixcrawler-rg `
  --name pixcrawler-test-YOUR-NAME-123 `
  --runtime "PYTHON:3.10" `
  --sku B1 `
  --location eastus
```

**Example with your name:**
```powershell
az webapp up `
  --resource-group pixcrawler-rg `
  --name pixcrawler-test-ahmed-456 `
  --runtime "PYTHON:3.10" `
  --sku B1 `
  --location eastus
```

### What Each Part Means

| Part                               | What It Means                                                     |
|------------------------------------|-------------------------------------------------------------------|
| `az webapp up`                     | "Azure, create and deploy a web app"                              |
| `--resource-group pixcrawler-rg`   | "Put it in a folder called 'pixcrawler-rg'"                       |
| `--name pixcrawler-test-ahmed-456` | "Name it 'pixcrawler-test-ahmed-456'" (must be unique worldwide!) |
| `--runtime "PYTHON:3.10"`          | "Use Python 3.10 to run it"                                       |
| `--sku B1`                         | "Use the 'Basic' tier (costs ~$13/month but we'll delete it)"     |
| `--location eastus`                | "Put the computer in the East US data center"                     |

### What You'll See

The command will take **5-10 minutes** and show:
```
Creating Resource group 'pixcrawler-rg' ...
Creating AppServicePlan 'ahmed_asp_1234' ...
Creating webapp 'pixcrawler-test-ahmed-456' ...
Configuring default logging for the app ...
Creating zip with contents of dir ...
Getting scm site credentials for zip deployment
Starting zip deployment ...
Deployment successful.
```

**At the end, you'll see:**
```
You can launch the app at http://pixcrawler-test-ahmed-456.azurewebsites.net
```

✅ **Your app is deployed!** (But not quite ready yet...)

---

## Step 5: Configure the Startup (2 minutes)

### Why This Step?
We need to tell Azure how to start your FastAPI app.

**Run this command** (replace with YOUR app name):
```powershell
az webapp config set `
  --resource-group pixcrawler-rg `
  --name pixcrawler-test-ahmed-456 `
  --startup-file "startup.sh"
```

**What it does:** Tells Azure to run the `startup.sh` file when starting your app.

### Wait for Restart

Azure will automatically restart your app. Wait **2-3 minutes**.

---

## Step 6: Check If It's Working (2 minutes)

### Test the Health Endpoint

**In your browser, go to:**
```
https://pixcrawler-test-ahmed-456.azurewebsites.net/health
```
(Replace `ahmed-456` with YOUR app name)

**You should see:**
```json
{"status":"healthy"}
```

✅ **It's working!**

### View the API Documentation

**In your browser, go to:**
```
https://pixcrawler-test-ahmed-456.azurewebsites.net/docs
```

You should see a nice interactive API documentation page (Swagger UI).

---

## Step 7: Test Your Two Questions (5 minutes)

### Use the PowerShell Test Script

**Run this command** (replace with YOUR app name):
```powershell
.\test_azure_api.ps1 -AppName "pixcrawler-test-ahmed-456"
```

**What it does:**
1. ✅ Checks health
2. ✅ Starts generating a small dataset (5 images)
3. ✅ Waits for it to complete
4. ✅ Lists all image URLs
5. ✅ Tests accessing an image

**This will take 2-3 minutes** (downloading images takes time).

### Expected Output

```
==========================================
Testing PixCrawler API on Azure
==========================================

[1/5] Testing health endpoint...
✅ Health check passed

[2/5] Starting dataset generation...
✅ Job started with ID: abc-123-def

[3/5] Checking job status...
   Attempt 1: Status = running
   Attempt 2: Status = running
   Attempt 3: Status = completed
✅ Job completed successfully!

[4/5] Listing generated images...
✅ Found 10 images

[5/5] Testing image access...
✅ Image accessible!

==========================================
🎉 TEST SUMMARY
==========================================
✅ BOTH QUESTIONS ANSWERED:
1. Azure CAN generate images locally on cloud
2. You CAN get URLs for each image
==========================================
```

---

## Step 8: View Your Images (Fun Part! 🎉)

### Get the Image URLs

**Run this command** (replace with YOUR job ID from the test):
```powershell
curl "https://pixcrawler-test-ahmed-456.azurewebsites.net/api/images/abc-123-def" | ConvertFrom-Json
```

**Or just open in browser:**
```
https://pixcrawler-test-ahmed-456.azurewebsites.net/api/images/abc-123-def
```

You'll see a JSON list of all images with their URLs!

### View an Image

**Copy one of the URLs from the list, like:**
```
/images/abc-123-def/animals/000001.jpg
```

**Open in browser:**
```
https://pixcrawler-test-ahmed-456.azurewebsites.net/images/abc-123-def/animals/000001.jpg
```

🎉 **You should see a cat image!** (or whatever you searched for)

---

## Step 9: Understanding What Happened

### Question 1: Did Azure generate images locally?

**YES!** ✅ Here's what happened:
1. Your FastAPI app ran on Azure's computer (not yours)
2. It downloaded images from Google/Bing
3. It saved them to Azure's disk (ephemeral storage)
4. It processed them (integrity checks, etc.)
5. All this happened "in the cloud" on Azure's servers

**The ephemeral storage part:**
- Azure gave your app some temporary disk space (like a scratch pad)
- Your images are saved there
- If Azure restarts your app, those files disappear
- **But for testing, this is perfect!** The files last long enough to verify everything works

### Question 2: Can you get URLs for images?

**YES!** ✅ Here's what happened:
1. Each image got a unique URL like: `/images/{job_id}/animals/000001.jpg`
2. Full URL: `https://your-app.azurewebsites.net/images/{job_id}/animals/000001.jpg`
3. You can share these URLs with anyone
4. They work in browsers, curl, anywhere
5. FastAPI serves the files directly from the ephemeral storage

**The limitation:**
- URLs only work while the app is running
- If app restarts, files (and URLs) are gone
- For production, you'd use Azure Blob Storage (permanent URLs)

---

## Step 10: Check What It Cost (Important!)

### View Your Spending

1. **Go to:** https://portal.azure.com
2. **Click:** "Cost Management + Billing" (left sidebar)
3. **Click:** "Cost analysis"
4. **See:** How much you've spent

**Expected cost for this test:**
- If you delete everything within 24 hours: **Less than $1**
- If you keep it running: **~$0.50 per day** (B1 tier)

**You have $200 free credit**, so don't worry!

---

## Step 11: Clean Up (Delete Everything)

### Why Delete?
Even though you have free credit, it's good practice to delete resources you're not using.

### Delete Everything in One Command

```powershell
az group delete --name pixcrawler-rg --yes --no-wait
```

**What it does:**
- Deletes the resource group
- Deletes everything inside it (app, plan, etc.)
- `--yes` means "don't ask for confirmation"
- `--no-wait` means "don't wait for it to finish"

**Verification:**
After 2-3 minutes, check in Azure Portal:
1. Go to: https://portal.azure.com
2. Click: "Resource groups" (left sidebar)
3. Verify: "pixcrawler-rg" is gone

✅ **All cleaned up!**

---

## 🎓 What You Learned

Congratulations! You just:
1. ✅ Created an Azure account
2. ✅ Deployed a Python web application to the cloud
3. ✅ Tested it works (both questions answered!)
4. ✅ Understood ephemeral vs permanent storage
5. ✅ Cleaned up resources

**You're no longer a beginner!** 🎉

---

## 🤔 Common Questions

### Q: Why did we use B1 tier instead of Free tier?
**A:** Free tier is very limited (60 min/day CPU time). B1 is cheap (~$13/month) but actually usable for testing.

### Q: What if I want to keep images permanently?
**A:** Use Azure Blob Storage. I can create a guide for that if you want!

### Q: Can I stop the app without deleting it?
**A:** Yes! Run:
```powershell
az webapp stop --resource-group pixcrawler-rg --name pixcrawler-test-ahmed-456
```
This stops the app (no charges) but keeps it for later.

### Q: How do I start it again?
**A:** Run:
```powershell
az webapp start --resource-group pixcrawler-rg --name pixcrawler-test-ahmed-456
```

### Q: What if something goes wrong?
**A:** Check the logs:
```powershell
az webapp log tail --resource-group pixcrawler-rg --name pixcrawler-test-ahmed-456
```
This shows real-time logs from your app.

### Q: Can I see my app in a web interface?
**A:** Yes! Go to https://portal.azure.com and click "App Services". You'll see your app with buttons to start/stop/delete/configure.

---

## 🆘 Troubleshooting

### "The name is already taken"
Someone else is using that app name. Try a different one:
```powershell
pixcrawler-test-ahmed-999
pixcrawler-test-myname-2025
pixcrawler-test-whatever-123
```

### "Command not found: az"
Azure CLI isn't installed or PowerShell needs restart. Close PowerShell and open it again.

### "You don't have permission"
Run `az login` again to make sure you're logged in.

### "Deployment failed"
Check the error message. Common issues:
- Wrong Python version → Make sure runtime.txt says `python-3.10`
- Missing files → Make sure you're in the PixCrawler directory
- Syntax error → Check startup.sh has Unix line endings (LF not CRLF)

### App shows "Application Error"
Wait 2-3 minutes after deployment. Azure needs time to install dependencies and start the app.

### Images not generating
Check logs with `az webapp log tail`. Look for errors about missing dependencies or network issues.

---

## 📚 Next Steps

### If You Want to Learn More

1. **Azure Portal Tour:** https://portal.azure.com - Click around, explore!
2. **Azure Free Services:** https://azure.microsoft.com/free/ - See what's free forever
3. **Azure Blob Storage Guide:** (I can create this if you want permanent image storage)

### If You Want to Build Production Version

Once you've verified it works, we can:
1. Add Azure Blob Storage for permanent images
2. Set up a database (PostgreSQL)
3. Add authentication
4. Set up custom domain
5. Add monitoring and alerts

Just let me know! 😊

---

## 🎉 Congratulations!

You've successfully:
- ✅ Deployed to Azure for the first time
- ✅ Answered both your questions
- ✅ Learned about cloud storage
- ✅ Became an Azure user!

**You did it!** 🚀

---

**Need help?** Just ask! I'm here to help you through any step.
