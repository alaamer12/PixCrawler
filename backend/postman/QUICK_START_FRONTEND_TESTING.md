# Quick Start: Frontend Integration Testing

Get started with frontend integration testing in 5 minutes.

## Prerequisites

- Node.js 18+ or Bun installed
- PixCrawler repository cloned

## Step 1: Run Setup Script (30 seconds)

### Linux/macOS
```bash
cd backend/postman
chmod +x setup-frontend-testing.sh
./setup-frontend-testing.sh
```

### Windows
```cmd
cd backend\postman
setup-frontend-testing.cmd
```

The script will:
- ✅ Check for required tools
- ✅ Install Prism CLI if needed
- ✅ Configure frontend environment
- ✅ Install dependencies

## Step 2: Start Mock Server (10 seconds)

```bash
cd backend/postman
prism mock openapi.json -p 4010
```

Expected output:
```
[CLI] ▶  start     Prism is listening on http://127.0.0.1:4010
```

**Keep this terminal open!**

## Step 3: Start Frontend (30 seconds)

Open a **new terminal**:

```bash
cd frontend

# Using Bun (preferred)
bun dev

# Using npm (fallback)
npm run dev
```

Expected output:
```
▲ Next.js 15.x
- Local:        http://localhost:3000
```

## Step 4: Open Browser (5 seconds)

Navigate to: **http://localhost:3000**

## Step 5: Start Testing (3 minutes)

### Quick Test: Create a Crawl Job

1. Navigate to the jobs page
2. Click "Create New Job"
3. Fill in:
   - Keywords: `laptop, computer`
   - Max Images: `1000`
4. Click "Create"

**Expected**: Job created with status "pending"

### Verify in DevTools

1. Open Browser DevTools (F12)
2. Go to Network tab
3. Look for: `POST http://localhost:4010/api/v1/jobs/`
4. Check response: Status 201, contains job object

✅ **Success!** Your frontend is connected to the mock server.

## What's Next?

### Full Testing

Follow the comprehensive guide:
📖 **[Frontend Integration Testing Guide](./FRONTEND_INTEGRATION_TESTING.md)**

### Use Checklist

Track your testing progress:
✅ **[Integration Test Checklist](./INTEGRATION_TEST_CHECKLIST.md)**

### Document Results

Fill out the test report:
📝 **[Test Report Template](./FRONTEND_INTEGRATION_TEST_REPORT.md)**

## Common Issues

### Issue: "Prism not found"

**Solution**: Install Prism manually
```bash
npm install -g @stoplight/prism-cli
```

### Issue: "Frontend can't connect"

**Solution**: Check environment variable
```bash
# In frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1
```

Restart frontend after changing `.env.local`

### Issue: "Port 4010 already in use"

**Solution**: Kill existing process or use different port
```bash
# Use different port
prism mock openapi.json -p 4011

# Update frontend .env.local
NEXT_PUBLIC_API_URL=http://localhost:4011/api/v1
```

### Issue: "CORS errors"

**Solution**: Prism handles CORS automatically. If you see CORS errors:
1. Verify Prism is running
2. Check the URL in frontend matches Prism port
3. Restart both Prism and frontend

## Testing Workflows

### 1. Crawl Jobs (2 minutes)
- ✅ Create job
- ✅ Start job
- ✅ Monitor progress
- ✅ Cancel job

### 2. Validation (2 minutes)
- ✅ Validate images
- ✅ Check results
- ✅ Analyze single image

### 3. Credits (2 minutes)
- ✅ Check balance
- ✅ View transactions
- ✅ Purchase credits

### 4. API Keys (2 minutes)
- ✅ List keys
- ✅ Create key
- ✅ Revoke key

**Total Testing Time**: ~10 minutes for all workflows

## Stopping

### Stop Mock Server
Press `Ctrl+C` in the Prism terminal

### Stop Frontend
Press `Ctrl+C` in the frontend terminal

### Restore Environment (Optional)
```bash
cd frontend
# Remove mock server configuration
# Restore original .env.local from backup if needed
```

## Tips

1. **Keep DevTools Open**: Monitor network requests in real-time
2. **Check Console**: Look for errors or warnings
3. **Test Systematically**: Follow the checklist to ensure complete coverage
4. **Document Issues**: Use the issue template in the testing guide
5. **Take Screenshots**: Capture any UI issues for reporting

## Resources

- 📖 [Full Testing Guide](./FRONTEND_INTEGRATION_TESTING.md)
- ✅ [Test Checklist](./INTEGRATION_TEST_CHECKLIST.md)
- 📝 [Test Report Template](./FRONTEND_INTEGRATION_TEST_REPORT.md)
- 📚 [Main README](./README.md)
- 🔧 [Troubleshooting Guide](./FRONTEND_INTEGRATION_TESTING.md#troubleshooting)

## Need Help?

1. Check the [Troubleshooting section](./FRONTEND_INTEGRATION_TESTING.md#troubleshooting)
2. Review the [Full Testing Guide](./FRONTEND_INTEGRATION_TESTING.md)
3. Check Prism documentation: https://stoplight.io/open-source/prism

---

**Ready to test?** Run the setup script and start testing in 5 minutes! 🚀
