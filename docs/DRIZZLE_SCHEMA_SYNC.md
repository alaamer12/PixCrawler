# Drizzle Schema Synchronization Summary

**Date:** 2025-11-01  
**Status:** ✅ Complete

## Overview

Updated the frontend Drizzle ORM schema (`frontend/lib/db/schema.ts`) to match the comprehensive backend SQLAlchemy models. The backend has evolved significantly with new features for billing, notifications, API keys, and usage tracking.

---

## 🆕 New Tables Added

### 1. **API Keys** (`api_keys`)
Programmatic access management with security features.

**Fields:**
- `id` (UUID, PK)
- `userId` (UUID, FK → profiles)
- `name` (varchar 200)
- `keyHash` (varchar 255, unique) - Hashed API key
- `keyPrefix` (varchar 20) - Key prefix for identification
- `status` (varchar 20) - active/revoked/expired
- `permissions` (jsonb) - Array of permissions
- `rateLimit` (integer) - Requests per hour
- `usageCount` (integer) - Total uses
- `lastUsedAt` (timestamp)
- `lastUsedIp` (varchar 45) - IPv6 compatible
- `expiresAt` (timestamp)
- `createdAt`, `updatedAt`

### 2. **Credit Accounts** (`credit_accounts`)
User billing and credit management.

**Fields:**
- `id` (UUID, PK)
- `userId` (UUID, FK → profiles, unique)
- `currentBalance` (integer)
- `monthlyUsage` (integer)
- `averageDailyUsage` (numeric 10,2)
- `autoRefillEnabled` (boolean)
- `refillThreshold` (integer)
- `refillAmount` (integer)
- `monthlyLimit` (integer)
- `createdAt`, `updatedAt`

### 3. **Credit Transactions** (`credit_transactions`)
Billing history and transaction tracking.

**Fields:**
- `id` (UUID, PK)
- `accountId` (UUID, FK → credit_accounts)
- `userId` (UUID, FK → profiles)
- `type` (varchar 20) - purchase/usage/refund/bonus
- `description` (text)
- `amount` (integer)
- `balanceAfter` (integer)
- `status` (varchar 20) - completed/pending/failed/cancelled
- `metadata` (jsonb)
- `createdAt`

### 4. **Notification Preferences** (`notification_preferences`)
User notification settings and preferences.

**Fields:**
- `id` (UUID, PK)
- `userId` (UUID, FK → profiles, unique)
- Channel preferences: `emailEnabled`, `pushEnabled`, `smsEnabled`
- Category preferences: `crawlJobsEnabled`, `datasetsEnabled`, `billingEnabled`, `securityEnabled`, `marketingEnabled`, `productUpdatesEnabled`
- `digestFrequency` (varchar 20) - realtime/daily/weekly/never
- `quietHoursStart`, `quietHoursEnd` (time)
- `createdAt`, `updatedAt`

### 5. **Usage Metrics** (`usage_metrics`)
Daily user activity and resource usage tracking.

**Fields:**
- `id` (UUID, PK)
- `userId` (UUID, FK → profiles)
- `metricDate` (date)
- `imagesProcessed`, `imagesLimit` (integer)
- `storageUsedGb`, `storageLimitGb` (numeric 10,2)
- `apiCalls`, `apiCallsLimit` (integer)
- `bandwidthUsedGb`, `bandwidthLimitGb` (numeric 10,2)
- `createdAt`

---

## 📝 Modified Tables

### **Crawl Jobs** (`crawl_jobs`)
Added **Chunk Tracking** fields for Celery task management:

**New Fields:**
- `totalChunks` (integer) - Total processing chunks
- `activeChunks` (integer) - Currently processing
- `completedChunks` (integer) - Successfully completed
- `failedChunks` (integer) - Failed chunks
- `taskIds` (jsonb) - Array of Celery task IDs

**Changed:**
- `maxImages` default: 100 → **1000**
- Removed: `searchEngine`, `config` (moved to backend-only)

### **Notifications** (`notifications`)
Enhanced notification system with better categorization:

**New Fields:**
- `category` (varchar 50) - crawl_job/payment/system/security/dataset/project
- `color` (varchar 20) - Display color
- `actionLabel` (varchar 100) - Action button text

**Changed:**
- `type`: Now represents severity (success/info/warning/error)
- `icon`: Clarified as Lucide icon name
- Removed: `iconColor` → replaced with `color`

### **Activity Logs** (`activity_logs`)
**Removed:**
- `ipAddress` field (moved to backend-only for security)

---

## 🔗 Relations Updated

### **Profiles Relations**
Added new relations:
- `apiKeys` (one-to-many)
- `creditAccount` (one-to-one)
- `notificationPreferences` (one-to-one)
- `usageMetrics` (one-to-many)

### **New Relations**
- `apiKeysRelations` → profiles
- `creditAccountsRelations` → profiles, transactions
- `creditTransactionsRelations` → account, user
- `notificationPreferencesRelations` → profiles
- `usageMetricsRelations` → profiles

---

## 📊 Type Exports Added

```typescript
export type APIKey = typeof apiKeys.$inferSelect;
export type NewAPIKey = typeof apiKeys.$inferInsert;
export type CreditAccount = typeof creditAccounts.$inferSelect;
export type NewCreditAccount = typeof creditAccounts.$inferInsert;
export type CreditTransaction = typeof creditTransactions.$inferSelect;
export type NewCreditTransaction = typeof creditTransactions.$inferInsert;
export type NotificationPreference = typeof notificationPreferences.$inferSelect;
export type NewNotificationPreference = typeof notificationPreferences.$inferInsert;
export type UsageMetric = typeof usageMetrics.$inferSelect;
export type NewUsageMetric = typeof usageMetrics.$inferInsert;
```

---

## 🎯 Backend Models Coverage

### ✅ Fully Synchronized
- **Core Models:** Profile, Project, CrawlJob, Image, ActivityLog
- **Credit Models:** CreditAccount, CreditTransaction
- **Notification Models:** Notification, NotificationPreference
- **API Models:** APIKey
- **Usage Models:** UsageMetric

### 📋 Backend-Only Models (Not in Frontend)
These models exist in backend but are intentionally excluded from frontend schema:
- **ChunkTrackingMixin** - Embedded in CrawlJob model
- **TimestampMixin** - Pattern applied to individual tables

---

## 🚀 Next Steps

### 1. Generate Migration
```bash
cd frontend
bun run db:generate
```

### 2. Review Migration
Check `frontend/drizzle/` for generated migration SQL.

### 3. Apply Migration
```bash
bun run db:migrate
```

### 4. Verify Schema
```bash
bun run db:studio
```

---

## 🔍 Key Differences: Backend vs Frontend

| Aspect | Backend (SQLAlchemy) | Frontend (Drizzle) |
|--------|---------------------|-------------------|
| **Constraints** | Full CHECK constraints, complex indexes | Basic constraints, simpler indexes |
| **Relationships** | Bidirectional with cascade | Drizzle relations for queries |
| **Mixins** | TimestampMixin, ChunkTrackingMixin | Fields duplicated per table |
| **Defaults** | Server-side defaults | Client-side defaults |
| **Type Safety** | Mapped[T] annotations | $inferSelect/$inferInsert |

---

## ⚠️ Important Notes

1. **Single Source of Truth:** Supabase PostgreSQL database
2. **RLS Required:** Frontend uses anon key with Row Level Security
3. **Backend Service Role:** Backend has full access via service role key
4. **No Direct Writes:** Frontend should prefer backend API for mutations
5. **Real-time:** Use Supabase subscriptions, not custom WebSockets

---

## 📚 Related Documentation

- Backend Models: `backend/models/__init__.py`
- Backend Schemas: `backend/schemas/`
- Frontend Schema: `frontend/lib/db/schema.ts`
- Architecture: `docs/ARCHITECTURE_SUMMARY.md`

---

## ✅ Verification Checklist

- [x] All backend models represented in Drizzle schema
- [x] Chunk tracking fields added to crawl_jobs
- [x] New tables: api_keys, credit_accounts, credit_transactions, notification_preferences, usage_metrics
- [x] Enhanced notifications with category and color
- [x] All relations properly defined
- [x] Type exports complete
- [ ] Migration generated (run `bun run db:generate`)
- [ ] Migration applied (run `bun run db:migrate`)
- [ ] Schema verified in Drizzle Studio

---

**Status:** Schema synchronization complete. Ready for migration generation and deployment.
