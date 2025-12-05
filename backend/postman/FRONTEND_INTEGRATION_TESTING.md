# Frontend Integration Testing Guide

This guide provides step-by-step instructions for testing the PixCrawler frontend with the Prism mock server.

## Prerequisites

- Node.js 18+ or Bun installed
- Prism CLI installed globally
- Frontend dependencies installed
- Mock server files ready (openapi.json)

## Setup Instructions

### 1. Install Prism Mock Server

```bash
# Using npm
npm install -g @stoplight/prism-cli

# Using bun
bun add -g @stoplight/prism-cli

# Verify installation
prism --version
```

### 2. Configure Frontend Environment

Create or update `frontend/.env.local` with the following configuration:

```env
# Point to Prism mock server
NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1

# Supabase Configuration (use test/development values)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# App Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development
```

**Important**: The `NEXT_PUBLIC_API_URL` must point to `http://localhost:4010/api/v1` to use the mock server.

### 3. Start the Mock Server

Open a terminal and start Prism:

```bash
cd backend/postman
prism mock openapi.json -p 4010
```

Expected output:
```
[CLI] …  awaiting  Starting Prism…
[CLI] ℹ  info      GET        http://127.0.0.1:4010/health
[CLI] ℹ  info      GET        http://127.0.0.1:4010/health/detailed
[CLI] ℹ  info      POST       http://127.0.0.1:4010/jobs/
...
[CLI] ✔  success   Prism is listening on http://127.0.0.1:4010
```

### 4. Start the Frontend

Open a new terminal and start the Next.js development server:

```bash
cd frontend

# Using bun (preferred)
bun dev

# Using npm (fallback)
npm run dev
```

The frontend should start at `http://localhost:3000`.

## Testing Workflows

### Test 1: Crawl Jobs Workflow

#### 1.1 Create a Crawl Job

1. Navigate to `http://localhost:3000/dashboard/jobs` (or the jobs page)
2. Click "Create New Job" or similar button
3. Fill in the form:
   - **Project**: Select or create a project
   - **Keywords**: Enter test keywords (e.g., "laptop", "computer")
   - **Max Images**: Enter a number (e.g., 1000)
   - **Engines**: Select search engines
4. Click "Create Job"

**Expected Result**:
- Job is created successfully
- UI shows the new job with status "pending"
- Job ID is displayed (UUID format)
- Success notification appears

**Verify**:
- Check browser DevTools Network tab
- Confirm POST request to `http://localhost:4010/api/v1/jobs/`
- Response status: 201 Created
- Response body contains job object with all fields

#### 1.2 Start a Job

1. Find the created job in the jobs list
2. Click "Start Job" button
3. Observe the UI update

**Expected Result**:
- Job status changes to "running"
- Task IDs are displayed (if shown in UI)
- Success notification appears

**Verify**:
- POST request to `http://localhost:4010/api/v1/jobs/{job_id}/start`
- Response status: 200 OK
- Response contains `task_ids` array and message

#### 1.3 Monitor Job Progress

1. Stay on the job details page or jobs list
2. Observe the progress indicators

**Expected Result**:
- Progress bar or percentage is displayed
- Chunk tracking metrics are shown:
  - Total chunks
  - Active chunks
  - Completed chunks
  - Failed chunks
- Image counts are displayed

**Verify**:
- GET request to `http://localhost:4010/api/v1/jobs/{job_id}/progress`
- Response status: 200 OK
- Response contains detailed progress metrics

#### 1.4 Cancel a Job

1. Click "Cancel Job" button
2. Confirm cancellation if prompted

**Expected Result**:
- Job status changes to "cancelled"
- Revoked task count is displayed
- Success notification appears

**Verify**:
- POST request to `http://localhost:4010/api/v1/jobs/{job_id}/cancel`
- Response status: 200 OK
- Response contains revoked count and status

### Test 2: Validation Workflow

#### 2.1 Validate Job Images

1. Navigate to a completed job
2. Click "Validate Images" or similar button
3. Select validation level (fast/medium/slow)
4. Confirm validation

**Expected Result**:
- Validation starts successfully
- Task IDs are displayed
- Images count is shown
- Success notification appears

**Verify**:
- POST request to `http://localhost:4010/api/v1/validation/job/{job_id}/`
- Request body contains `validation_level`
- Response status: 200 OK
- Response contains task_ids and images_count

#### 2.2 Check Validation Results

1. Navigate to validation results page
2. View aggregated statistics

**Expected Result**:
- Total images count displayed
- Valid images count displayed
- Invalid images count displayed
- Duplicate images count displayed
- Validation statistics are accurate

**Verify**:
- GET request to `http://localhost:4010/api/v1/validation/results/{job_id}/`
- Response status: 200 OK
- Response contains aggregated stats

#### 2.3 Analyze Single Image

1. Navigate to image details or upload page
2. Select an image to analyze
3. Click "Analyze" button

**Expected Result**:
- Validation results are displayed:
  - is_valid status
  - is_duplicate status
  - Dimensions
  - Format
  - Hash value

**Verify**:
- POST request to `http://localhost:4010/api/v1/validation/analyze/`
- Request body contains image_url or image_data
- Response status: 200 OK
- Response contains validation details

### Test 3: Credits Workflow

#### 3.1 Check Credit Balance

1. Navigate to billing or credits page
2. View credit balance

**Expected Result**:
- Current balance is displayed
- Monthly usage is shown
- Monthly limit is displayed
- Auto-refill settings are visible

**Verify**:
- GET request to `http://localhost:4010/api/v1/credits/balance`
- Response status: 200 OK
- Response contains balance, usage, limits, and auto-refill settings

#### 3.2 View Transaction History

1. Navigate to transactions page
2. View transaction list

**Expected Result**:
- Transactions are displayed in a table/list
- Each transaction shows:
  - Type (purchase, usage, refund, bonus)
  - Amount
  - Status
  - Date/timestamp
- Pagination controls are visible

**Verify**:
- GET request to `http://localhost:4010/api/v1/credits/transactions`
- Response status: 200 OK
- Response contains paginated transaction data with meta object

#### 3.3 Purchase Credits

1. Click "Purchase Credits" button
2. Select credit amount
3. Enter payment details (mock)
4. Confirm purchase

**Expected Result**:
- Purchase is processed successfully
- Transaction details are displayed
- Updated balance is shown
- Success notification appears

**Verify**:
- POST request to `http://localhost:4010/api/v1/credits/purchase`
- Request body contains amount, payment_method, payment_token
- Response status: 201 Created
- Response contains transaction details and updated balance

### Test 4: API Keys Workflow

#### 4.1 List API Keys

1. Navigate to API keys page
2. View existing API keys

**Expected Result**:
- API keys are displayed in a table/list
- Each key shows:
  - Name
  - Key prefix (e.g., "pk_live_")
  - Permissions
  - Rate limit
  - Usage statistics
  - Created date
  - Expiration date

**Verify**:
- GET request to `http://localhost:4010/api/v1/api-keys/`
- Response status: 200 OK
- Response contains array of API keys with usage statistics

#### 4.2 Create API Key

1. Click "Create API Key" button
2. Fill in the form:
  - Name
  - Permissions (read, write)
  - Rate limit
  - Expiration date (optional)
3. Click "Create"

**Expected Result**:
- API key is created successfully
- Full key value is displayed (shown only once)
- Warning message about secure storage is shown
- Key details are displayed
- Success notification appears

**Verify**:
- POST request to `http://localhost:4010/api/v1/api-keys/`
- Request body contains name, permissions, rate_limit, expires_at
- Response status: 201 Created
- Response contains full key value and details

#### 4.3 Revoke API Key

1. Find an API key in the list
2. Click "Revoke" or "Delete" button
3. Confirm revocation

**Expected Result**:
- API key is revoked successfully
- Key is removed from the list or marked as revoked
- Success notification appears

**Verify**:
- DELETE request to `http://localhost:4010/api/v1/api-keys/{key_id}`
- Response status: 200 OK
- Response contains revocation confirmation

## UI Rendering Verification

### General UI Checks

For each workflow, verify the following:

1. **Data Display**:
   - All fields from mock responses are displayed correctly
   - UUIDs are formatted properly
   - Timestamps are displayed in readable format
   - Numbers are formatted correctly (with commas, decimals)

2. **Loading States**:
   - Loading indicators appear during API calls
   - Skeleton loaders or spinners are shown
   - UI doesn't freeze or become unresponsive

3. **Error Handling**:
   - No console errors in browser DevTools
   - No React errors or warnings
   - No TypeScript errors

4. **Responsive Design**:
   - UI renders correctly on desktop
   - UI is usable on tablet (if applicable)
   - UI is usable on mobile (if applicable)

5. **Notifications**:
   - Success notifications appear for successful operations
   - Notifications are dismissible
   - Notifications auto-dismiss after a few seconds

6. **Navigation**:
   - All links work correctly
   - Back button works as expected
   - Breadcrumbs are accurate (if present)

## Data Format Verification

### Common Data Formats to Check

1. **UUIDs**:
   - Format: `550e8400-e29b-41d4-a716-446655440000`
   - Displayed correctly in UI
   - Used correctly in API calls

2. **Timestamps**:
   - Format: ISO 8601 (`2025-12-05T10:00:00Z`)
   - Displayed as human-readable dates
   - Timezone handling is correct

3. **Status Values**:
   - Consistent enum values (pending, running, completed, failed, cancelled)
   - Displayed with appropriate styling (colors, icons)

4. **Pagination**:
   - Meta object structure: `{ total, page, limit, pages }`
   - Pagination controls work correctly
   - Page numbers are accurate

5. **Response Structure**:
   - Single objects: `{ data: {...} }`
   - Collections: `{ data: [...], meta: {...} }`
   - Frontend correctly extracts data from these structures

## Known Limitations

### Mock Server Limitations

1. **No Authentication**:
   - Mock server doesn't validate JWT tokens
   - All requests succeed regardless of authentication
   - Test authentication flows separately with real backend

2. **Static Responses**:
   - Mock server returns predefined examples
   - Data doesn't change between requests
   - Progress values don't update automatically

3. **No State Management**:
   - Creating a job doesn't affect job list
   - Deleting a resource doesn't remove it from lists
   - Each request is independent

4. **Success Only**:
   - Mock server only returns success responses (200, 201)
   - Error cases (400, 401, 404, 500) are not tested
   - Test error handling separately

### Frontend Limitations

1. **Real-time Updates**:
   - Supabase real-time subscriptions won't work with mock server
   - Progress updates won't be automatic
   - Manual refresh required to see changes

2. **Authentication**:
   - Supabase Auth still requires real credentials
   - Mock server doesn't replace Supabase Auth
   - Use test Supabase project for authentication

## Troubleshooting

### Issue: Frontend can't connect to mock server

**Symptoms**:
- Network errors in browser console
- "Failed to fetch" errors
- CORS errors

**Solutions**:
1. Verify Prism is running on port 4010
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Restart frontend after changing environment variables
4. Check for CORS issues (Prism should handle CORS automatically)

### Issue: Mock responses don't match frontend expectations

**Symptoms**:
- UI shows "undefined" or "null" values
- TypeScript errors in console
- Data not displaying correctly

**Solutions**:
1. Compare OpenAPI response examples with frontend TypeScript interfaces
2. Check field names match exactly (case-sensitive)
3. Verify nested object structures
4. Update OpenAPI examples or frontend interfaces as needed

### Issue: Prism returns 404 for valid endpoints

**Symptoms**:
- 404 Not Found errors
- "No matching operation" errors from Prism

**Solutions**:
1. Verify endpoint path matches OpenAPI spec exactly
2. Check HTTP method (GET, POST, etc.)
3. Ensure path parameters are in correct format
4. Validate OpenAPI spec with Swagger Editor

### Issue: Frontend authentication fails

**Symptoms**:
- "Unauthorized" errors
- Redirect to login page
- Token errors

**Solutions**:
1. Remember: Mock server doesn't handle authentication
2. Use real Supabase project for authentication
3. Ensure Supabase environment variables are set correctly
4. Check Supabase Auth is working independently

## Documentation of Issues

### Issue Tracking Template

When you encounter issues, document them using this template:

```markdown
## Issue: [Brief Description]

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Workflow**: [e.g., Crawl Jobs - Create Job]

### Description
[Detailed description of the issue]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happened]

### Screenshots
[Attach screenshots if applicable]

### Network Request
- **URL**: [Full URL]
- **Method**: [GET/POST/etc.]
- **Request Body**: [JSON]
- **Response Status**: [200/404/etc.]
- **Response Body**: [JSON]

### Console Errors
```
[Paste console errors here]
```

### Proposed Solution
[How to fix this issue]

### Priority
[High/Medium/Low]
```

## Test Results Summary

After completing all tests, fill out this summary:

### Test Execution Summary

**Date**: ___________
**Tester**: ___________
**Duration**: ___________

| Workflow | Status | Issues Found | Notes |
|----------|--------|--------------|-------|
| Crawl Jobs - Create | ☐ Pass ☐ Fail | | |
| Crawl Jobs - Start | ☐ Pass ☐ Fail | | |
| Crawl Jobs - Progress | ☐ Pass ☐ Fail | | |
| Crawl Jobs - Cancel | ☐ Pass ☐ Fail | | |
| Validation - Job Images | ☐ Pass ☐ Fail | | |
| Validation - Results | ☐ Pass ☐ Fail | | |
| Validation - Single Image | ☐ Pass ☐ Fail | | |
| Credits - Balance | ☐ Pass ☐ Fail | | |
| Credits - Transactions | ☐ Pass ☐ Fail | | |
| Credits - Purchase | ☐ Pass ☐ Fail | | |
| API Keys - List | ☐ Pass ☐ Fail | | |
| API Keys - Create | ☐ Pass ☐ Fail | | |
| API Keys - Revoke | ☐ Pass ☐ Fail | | |

### Overall Assessment

**UI Rendering**: ☐ Excellent ☐ Good ☐ Fair ☐ Poor

**Data Format Compatibility**: ☐ Excellent ☐ Good ☐ Fair ☐ Poor

**User Experience**: ☐ Excellent ☐ Good ☐ Fair ☐ Poor

### Critical Issues
[List any critical issues that block functionality]

### Minor Issues
[List any minor issues or improvements]

### Recommendations
[Recommendations for improvements]

## Next Steps

After completing frontend integration testing:

1. **Document all issues** found during testing
2. **Create GitHub issues** for bugs and improvements
3. **Update OpenAPI spec** if data format mismatches are found
4. **Update frontend interfaces** if needed
5. **Retest** after fixes are applied
6. **Sign off** on the integration testing phase

## Conclusion

This frontend integration testing validates that:
- ✅ Frontend can connect to mock server
- ✅ All API endpoints are accessible
- ✅ Mock responses match frontend expectations
- ✅ UI renders correctly with mock data
- ✅ User workflows function as expected
- ✅ Data formats are compatible

Once all tests pass, the mock server is ready for frontend development use.
