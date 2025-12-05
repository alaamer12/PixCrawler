# Frontend Integration Testing Checklist

Quick reference checklist for testing the PixCrawler frontend with Prism mock server.

## Pre-Test Setup

- [ ] Prism CLI installed (`npm install -g @stoplight/prism-cli`)
- [ ] Frontend `.env.local` configured with `NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1`
- [ ] Prism mock server running (`prism mock openapi.json -p 4010`)
- [ ] Frontend development server running (`bun dev` or `npm run dev`)
- [ ] Browser DevTools open (Network tab)

## Test 1: Crawl Jobs Workflow

### Create Job
- [ ] Navigate to jobs page
- [ ] Click "Create New Job"
- [ ] Fill form with test data
- [ ] Submit form
- [ ] ✓ Job created with status "pending"
- [ ] ✓ Job ID displayed (UUID format)
- [ ] ✓ Success notification shown
- [ ] ✓ POST to `/api/v1/jobs/` returns 201

### Start Job
- [ ] Click "Start Job" button
- [ ] ✓ Job status changes to "running"
- [ ] ✓ Task IDs displayed
- [ ] ✓ Success notification shown
- [ ] ✓ POST to `/api/v1/jobs/{job_id}/start` returns 200

### Monitor Progress
- [ ] View job progress page
- [ ] ✓ Progress percentage displayed
- [ ] ✓ Chunk metrics shown (total, active, completed, failed)
- [ ] ✓ Image counts displayed
- [ ] ✓ GET to `/api/v1/jobs/{job_id}/progress` returns 200

### Cancel Job
- [ ] Click "Cancel Job" button
- [ ] Confirm cancellation
- [ ] ✓ Job status changes to "cancelled"
- [ ] ✓ Revoked count displayed
- [ ] ✓ Success notification shown
- [ ] ✓ POST to `/api/v1/jobs/{job_id}/cancel` returns 200

## Test 2: Validation Workflow

### Validate Job Images
- [ ] Navigate to completed job
- [ ] Click "Validate Images"
- [ ] Select validation level
- [ ] Confirm validation
- [ ] ✓ Validation started successfully
- [ ] ✓ Task IDs displayed
- [ ] ✓ Images count shown
- [ ] ✓ POST to `/api/v1/validation/job/{job_id}/` returns 200

### Check Results
- [ ] Navigate to validation results
- [ ] ✓ Total images count displayed
- [ ] ✓ Valid images count displayed
- [ ] ✓ Invalid images count displayed
- [ ] ✓ Duplicate images count displayed
- [ ] ✓ GET to `/api/v1/validation/results/{job_id}/` returns 200

### Analyze Single Image
- [ ] Navigate to image analysis page
- [ ] Select/upload image
- [ ] Click "Analyze"
- [ ] ✓ Validation results displayed (is_valid, is_duplicate, dimensions, format, hash)
- [ ] ✓ POST to `/api/v1/validation/analyze/` returns 200

## Test 3: Credits Workflow

### Check Balance
- [ ] Navigate to credits/billing page
- [ ] ✓ Current balance displayed
- [ ] ✓ Monthly usage shown
- [ ] ✓ Monthly limit displayed
- [ ] ✓ Auto-refill settings visible
- [ ] ✓ GET to `/api/v1/credits/balance` returns 200

### View Transactions
- [ ] Navigate to transactions page
- [ ] ✓ Transactions displayed in table/list
- [ ] ✓ Each transaction shows type, amount, status, date
- [ ] ✓ Pagination controls visible
- [ ] ✓ GET to `/api/v1/credits/transactions` returns 200

### Purchase Credits
- [ ] Click "Purchase Credits"
- [ ] Select amount
- [ ] Enter payment details (mock)
- [ ] Confirm purchase
- [ ] ✓ Purchase processed successfully
- [ ] ✓ Transaction details displayed
- [ ] ✓ Updated balance shown
- [ ] ✓ POST to `/api/v1/credits/purchase` returns 201

## Test 4: API Keys Workflow

### List Keys
- [ ] Navigate to API keys page
- [ ] ✓ API keys displayed in table/list
- [ ] ✓ Each key shows name, prefix, permissions, rate limit, usage, dates
- [ ] ✓ GET to `/api/v1/api-keys/` returns 200

### Create Key
- [ ] Click "Create API Key"
- [ ] Fill form (name, permissions, rate limit, expiration)
- [ ] Click "Create"
- [ ] ✓ Key created successfully
- [ ] ✓ Full key value displayed (shown once)
- [ ] ✓ Warning about secure storage shown
- [ ] ✓ POST to `/api/v1/api-keys/` returns 201

### Revoke Key
- [ ] Find key in list
- [ ] Click "Revoke" or "Delete"
- [ ] Confirm revocation
- [ ] ✓ Key revoked successfully
- [ ] ✓ Key removed or marked as revoked
- [ ] ✓ DELETE to `/api/v1/api-keys/{key_id}` returns 200

## UI Rendering Checks

### Data Display
- [ ] ✓ All fields from responses displayed correctly
- [ ] ✓ UUIDs formatted properly
- [ ] ✓ Timestamps in readable format
- [ ] ✓ Numbers formatted correctly

### Loading States
- [ ] ✓ Loading indicators appear during API calls
- [ ] ✓ Skeleton loaders or spinners shown
- [ ] ✓ UI remains responsive

### Error Handling
- [ ] ✓ No console errors in DevTools
- [ ] ✓ No React errors or warnings
- [ ] ✓ No TypeScript errors

### Notifications
- [ ] ✓ Success notifications appear
- [ ] ✓ Notifications are dismissible
- [ ] ✓ Notifications auto-dismiss

### Navigation
- [ ] ✓ All links work correctly
- [ ] ✓ Back button works
- [ ] ✓ Breadcrumbs accurate

## Data Format Verification

### UUIDs
- [ ] ✓ Format: `550e8400-e29b-41d4-a716-446655440000`
- [ ] ✓ Displayed correctly in UI
- [ ] ✓ Used correctly in API calls

### Timestamps
- [ ] ✓ Format: ISO 8601 (`2025-12-05T10:00:00Z`)
- [ ] ✓ Displayed as human-readable dates
- [ ] ✓ Timezone handling correct

### Status Values
- [ ] ✓ Consistent enums (pending, running, completed, failed, cancelled)
- [ ] ✓ Displayed with appropriate styling

### Pagination
- [ ] ✓ Meta object structure correct: `{ total, page, limit, pages }`
- [ ] ✓ Pagination controls work
- [ ] ✓ Page numbers accurate

### Response Structure
- [ ] ✓ Single objects: `{ data: {...} }`
- [ ] ✓ Collections: `{ data: [...], meta: {...} }`
- [ ] ✓ Frontend extracts data correctly

## Issues Found

### Critical Issues
```
[Document critical issues here]
```

### Minor Issues
```
[Document minor issues here]
```

### Data Format Mismatches
```
[Document any mismatches between mock responses and frontend expectations]
```

## Test Summary

**Date**: ___________
**Tester**: ___________
**Duration**: ___________

**Overall Status**: ☐ Pass ☐ Fail ☐ Partial

**Tests Passed**: ___ / 13

**Critical Issues**: ___
**Minor Issues**: ___

**Ready for Development**: ☐ Yes ☐ No

## Sign-off

**Tester Signature**: ___________
**Date**: ___________

**Notes**:
```
[Additional notes or observations]
```
