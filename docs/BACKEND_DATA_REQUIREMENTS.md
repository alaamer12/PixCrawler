# Backend Data Requirements for Profile & Notifications

This document outlines all data structures and API endpoints required by the frontend Profile and Notifications pages.

---

## 1. User Profile Data

### Database Schema: `profiles` table

```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  
  -- Basic Information
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  full_name VARCHAR(200),
  avatar_url TEXT,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  
  -- Professional Information
  bio TEXT,
  company VARCHAR(200),
  job_title VARCHAR(200),
  
  -- Location & Contact
  location VARCHAR(200),
  website TEXT,
  timezone VARCHAR(100) DEFAULT 'UTC',
  language VARCHAR(10) DEFAULT 'en',
  
  -- Social Links
  linkedin_username VARCHAR(100),
  github_username VARCHAR(100),
  twitter_username VARCHAR(100),
  
  -- Privacy & Preferences
  public_profile BOOLEAN DEFAULT false,
  email_notifications BOOLEAN DEFAULT true,
  marketing_emails BOOLEAN DEFAULT false,
  
  -- Metadata
  onboarding_completed BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

#### GET `/api/v1/profile`
**Response:**
```json
{
  "id": "uuid",
  "firstName": "string",
  "lastName": "string",
  "fullName": "string",
  "avatarUrl": "string",
  "email": "string",
  "phone": "string",
  "bio": "string",
  "company": "string",
  "jobTitle": "string",
  "location": "string",
  "website": "string",
  "timezone": "string",
  "language": "string",
  "linkedin": "string",
  "github": "string",
  "twitter": "string",
  "publicProfile": boolean,
  "emailNotifications": boolean,
  "marketingEmails": boolean,
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601"
}
```

#### PATCH `/api/v1/profile`
**Request:**
```json
{
  "firstName": "string",
  "lastName": "string",
  "phone": "string",
  "bio": "string",
  "company": "string",
  "jobTitle": "string",
  "location": "string",
  "website": "string",
  "timezone": "string",
  "language": "string",
  "linkedin": "string",
  "github": "string",
  "twitter": "string",
  "publicProfile": boolean,
  "emailNotifications": boolean,
  "marketingEmails": boolean
}
```

#### POST `/api/v1/profile/avatar`
**Request:** `multipart/form-data`
- `file`: Image file (max 5MB, jpg/png/webp)

**Response:**
```json
{
  "avatarUrl": "string"
}
```

#### DELETE `/api/v1/account`
**Request:** None (requires authentication)
**Response:**
```json
{
  "message": "Account deleted successfully"
}
```

---

## 2. Credits & Billing Data

### Database Schema: `credit_accounts` table

```sql
CREATE TABLE credit_accounts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  current_balance INTEGER NOT NULL DEFAULT 0,
  monthly_usage INTEGER NOT NULL DEFAULT 0,
  average_daily_usage DECIMAL(10,2) DEFAULT 0,
  
  -- Auto-refill settings
  auto_refill_enabled BOOLEAN DEFAULT false,
  refill_threshold INTEGER DEFAULT 100,
  refill_amount INTEGER DEFAULT 500,
  monthly_limit INTEGER DEFAULT 2000,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Database Schema: `credit_transactions` table

```sql
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  type VARCHAR(20) NOT NULL, -- 'purchase', 'usage', 'refund', 'bonus'
  description TEXT NOT NULL,
  amount INTEGER NOT NULL, -- positive for credits added, negative for usage
  balance_after INTEGER NOT NULL,
  status VARCHAR(20) DEFAULT 'completed', -- 'completed', 'pending', 'failed'
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

#### GET `/api/v1/credits/balance`
**Response:**
```json
{
  "currentBalance": 1250,
  "monthlyUsage": 750,
  "averageDailyUsage": 25,
  "autoRefillEnabled": true,
  "refillThreshold": 100,
  "refillAmount": 500,
  "monthlyLimit": 2000
}
```

#### GET `/api/v1/credits/transactions`
**Query Parameters:**
- `limit`: number (default: 50)
- `offset`: number (default: 0)
- `type`: 'purchase' | 'usage' | 'refund' | 'bonus' (optional)

**Response:**
```json
{
  "transactions": [
    {
      "id": "uuid",
      "date": "ISO8601",
      "type": "purchase",
      "description": "Credit purchase - 500 credits",
      "amount": 500,
      "balance": 1250,
      "status": "completed"
    }
  ],
  "total": 150,
  "hasMore": true
}
```

#### GET `/api/v1/credits/usage-history`
**Query Parameters:**
- `period`: '7d' | '30d' | '90d' | '1y' (default: '30d')

**Response:**
```json
{
  "data": [
    {
      "date": "2024-10-01",
      "usage": 45,
      "purchases": 0
    }
  ],
  "summary": {
    "totalUsage": 750,
    "totalPurchases": 1000,
    "averageDaily": 25
  }
}
```

#### PATCH `/api/v1/credits/auto-refill`
**Request:**
```json
{
  "enabled": boolean,
  "threshold": number,
  "amount": number,
  "monthlyLimit": number
}
```

#### POST `/api/v1/credits/purchase`
**Request:**
```json
{
  "packageId": "string",
  "credits": number,
  "price": number
}
```

---

## 3. Usage & Analytics Data

### Database Schema: `usage_metrics` table

```sql
CREATE TABLE usage_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  metric_date DATE NOT NULL,
  
  -- Core Metrics
  images_processed INTEGER DEFAULT 0,
  storage_used_gb DECIMAL(10,2) DEFAULT 0,
  api_calls INTEGER DEFAULT 0,
  bandwidth_used_gb DECIMAL(10,2) DEFAULT 0,
  
  -- Limits
  images_limit INTEGER DEFAULT 10000,
  storage_limit_gb DECIMAL(10,2) DEFAULT 100,
  api_calls_limit INTEGER DEFAULT 50000,
  bandwidth_limit_gb DECIMAL(10,2) DEFAULT 500,
  
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id, metric_date)
);
```

### API Endpoints

#### GET `/api/v1/usage/metrics`
**Query Parameters:**
- `period`: '7d' | '30d' | '90d' (default: '30d')

**Response:**
```json
{
  "metrics": [
    {
      "name": "Images Processed",
      "current": 7523,
      "limit": 10000,
      "unit": "images",
      "trend": "up",
      "trendValue": 12.5
    },
    {
      "name": "Storage Used",
      "current": 42.7,
      "limit": 100,
      "unit": "GB",
      "trend": "up",
      "trendValue": 8.3
    },
    {
      "name": "API Calls",
      "current": 15234,
      "limit": 50000,
      "unit": "calls",
      "trend": "down",
      "trendValue": 5.2
    },
    {
      "name": "Bandwidth",
      "current": 125.8,
      "limit": 500,
      "unit": "GB",
      "trend": "stable",
      "trendValue": 0.5
    }
  ]
}
```

#### GET `/api/v1/usage/history`
**Query Parameters:**
- `period`: '7d' | '30d' | '90d' (default: '30d')
- `metric`: 'images' | 'storage' | 'bandwidth' | 'apiCalls' | 'all' (default: 'all')

**Response:**
```json
{
  "data": [
    {
      "date": "2024-10-01",
      "images": 245,
      "storage": 1.2,
      "bandwidth": 3.5,
      "apiCalls": 523
    }
  ]
}
```

---

## 4. API Keys Management

### Database Schema: `api_keys` table

```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  name VARCHAR(200) NOT NULL,
  key_hash VARCHAR(255) NOT NULL, -- bcrypt hash of the key
  key_prefix VARCHAR(20) NOT NULL, -- e.g., 'pk_live_', 'pk_test_'
  status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'expired'
  permissions JSONB NOT NULL DEFAULT '[]',
  rate_limit INTEGER DEFAULT 1000,
  usage_count INTEGER DEFAULT 0,
  last_used_at TIMESTAMP,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

#### GET `/api/v1/api-keys`
**Response:**
```json
{
  "keys": [
    {
      "id": "uuid",
      "name": "Production API",
      "keyPrefix": "pk_live_",
      "created": "ISO8601",
      "lastUsed": "ISO8601",
      "status": "active",
      "permissions": ["read:images", "write:images"],
      "rateLimit": 1000,
      "usage": 523,
      "expiresAt": "ISO8601" // optional
    }
  ]
}
```

#### POST `/api/v1/api-keys`
**Request:**
```json
{
  "name": "string",
  "permissions": ["string"],
  "expiresAt": "ISO8601" // optional
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "key": "pk_live_51234567890abcdefghijklmnop", // Only returned once
  "permissions": ["string"],
  "rateLimit": 1000
}
```

#### PATCH `/api/v1/api-keys/:id`
**Request:**
```json
{
  "name": "string", // optional
  "permissions": ["string"], // optional
  "status": "active" | "inactive" // optional
}
```

#### POST `/api/v1/api-keys/:id/regenerate`
**Response:**
```json
{
  "key": "pk_live_new_key_here" // Only returned once
}
```

#### DELETE `/api/v1/api-keys/:id`
**Response:**
```json
{
  "message": "API key deleted successfully"
}
```

---

## 5. Notifications System

### Database Schema: `notifications` table

```sql
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  type VARCHAR(50) NOT NULL, -- 'success', 'info', 'warning', 'error'
  category VARCHAR(50), -- 'crawl_job', 'payment', 'system', 'security'
  icon VARCHAR(50), -- lucide icon name
  color VARCHAR(20), -- 'green', 'blue', 'red', 'yellow'
  action_url TEXT,
  action_label VARCHAR(100),
  is_read BOOLEAN DEFAULT false,
  read_at TIMESTAMP,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

### API Endpoints

#### GET `/api/v1/notifications`
**Query Parameters:**
- `unread`: boolean (optional, filter unread only)
- `category`: string (optional)
- `limit`: number (default: 50)
- `offset`: number (default: 0)

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "title": "Crawl job completed",
      "message": "Your \"Cat Breeds\" dataset is ready",
      "type": "success",
      "category": "crawl_job",
      "icon": "circle-check-big",
      "color": "green",
      "actionUrl": "/dashboard/datasets/123",
      "actionLabel": "View Dataset",
      "isRead": false,
      "readAt": null,
      "createdAt": "ISO8601"
    }
  ],
  "unreadCount": 5,
  "total": 150
}
```

#### GET `/api/v1/notifications/:id`
**Response:**
```json
{
  "id": 1,
  "title": "string",
  "message": "string",
  "type": "success",
  "category": "crawl_job",
  "icon": "circle-check-big",
  "color": "green",
  "actionUrl": "string",
  "actionLabel": "string",
  "isRead": false,
  "readAt": null,
  "metadata": {},
  "createdAt": "ISO8601"
}
```

#### PATCH `/api/v1/notifications/:id`
**Request:**
```json
{
  "isRead": boolean
}
```

#### POST `/api/v1/notifications/mark-all-read`
**Response:**
```json
{
  "message": "All notifications marked as read",
  "count": 5
}
```

#### DELETE `/api/v1/notifications/:id`
**Response:**
```json
{
  "message": "Notification deleted successfully"
}
```

#### DELETE `/api/v1/notifications`
**Query Parameters:**
- `read`: boolean (optional, delete only read notifications)

**Response:**
```json
{
  "message": "Notifications deleted successfully",
  "count": 10
}
```

---

## 6. Notification Settings

### Database Schema: `notification_preferences` table

```sql
CREATE TABLE notification_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) UNIQUE,
  
  -- Channels
  email_enabled BOOLEAN DEFAULT true,
  push_enabled BOOLEAN DEFAULT false,
  sms_enabled BOOLEAN DEFAULT false,
  
  -- Categories
  crawl_jobs_enabled BOOLEAN DEFAULT true,
  datasets_enabled BOOLEAN DEFAULT true,
  billing_enabled BOOLEAN DEFAULT true,
  security_enabled BOOLEAN DEFAULT true,
  marketing_enabled BOOLEAN DEFAULT false,
  product_updates_enabled BOOLEAN DEFAULT true,
  
  -- Frequency
  digest_frequency VARCHAR(20) DEFAULT 'daily', -- 'realtime', 'daily', 'weekly', 'never'
  quiet_hours_start TIME,
  quiet_hours_end TIME,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

#### GET `/api/v1/notifications/preferences`
**Response:**
```json
{
  "emailEnabled": true,
  "pushEnabled": false,
  "smsEnabled": false,
  "categories": {
    "crawlJobs": true,
    "datasets": true,
    "billing": true,
    "security": true,
    "marketing": false,
    "productUpdates": true
  },
  "digestFrequency": "daily",
  "quietHours": {
    "start": "22:00",
    "end": "08:00"
  }
}
```

#### PATCH `/api/v1/notifications/preferences`
**Request:**
```json
{
  "emailEnabled": boolean,
  "pushEnabled": boolean,
  "categories": {
    "crawlJobs": boolean,
    "datasets": boolean,
    "billing": boolean,
    "security": boolean,
    "marketing": boolean,
    "productUpdates": boolean
  },
  "digestFrequency": "realtime" | "daily" | "weekly" | "never"
}
```

---

## 7. Settings & Preferences

### Database Schema: `user_settings` table

```sql
CREATE TABLE user_settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) UNIQUE,
  
  -- Appearance
  theme VARCHAR(20) DEFAULT 'system', -- 'light', 'dark', 'system'
  compact_mode BOOLEAN DEFAULT false,
  
  -- Workspace
  default_view VARCHAR(20) DEFAULT 'grid', -- 'grid', 'list'
  items_per_page INTEGER DEFAULT 20,
  show_thumbnails BOOLEAN DEFAULT true,
  auto_expand_folders BOOLEAN DEFAULT false,
  confirm_delete BOOLEAN DEFAULT true,
  
  -- Privacy
  show_activity BOOLEAN DEFAULT true,
  allow_analytics BOOLEAN DEFAULT true,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

#### GET `/api/v1/settings`
**Response:**
```json
{
  "theme": "system",
  "compactMode": false,
  "defaultView": "grid",
  "itemsPerPage": 20,
  "showThumbnails": true,
  "autoExpandFolders": false,
  "confirmDelete": true,
  "showActivity": true,
  "allowAnalytics": true
}
```

#### PATCH `/api/v1/settings`
**Request:**
```json
{
  "theme": "light" | "dark" | "system",
  "compactMode": boolean,
  "defaultView": "grid" | "list",
  "itemsPerPage": number,
  "showThumbnails": boolean,
  "autoExpandFolders": boolean,
  "confirmDelete": boolean,
  "showActivity": boolean,
  "allowAnalytics": boolean
}
```

---

## Implementation Priority

### Phase 1 (Critical)
1. User Profile endpoints (GET, PATCH)
2. Notifications endpoints (GET, PATCH, DELETE)
3. API Keys management (GET, POST, DELETE)

### Phase 2 (Important)
4. Credits & Billing (balance, transactions)
5. Usage metrics (current usage, limits)
6. Notification preferences

### Phase 3 (Nice to have)
7. Usage history with charts data
8. Credit usage analytics
9. Settings management

---

## Authentication & Authorization

All endpoints require:
- **Authentication**: Bearer token in `Authorization` header
- **User Context**: Extract `user_id` from JWT token
- **RLS**: Row-level security policies on all tables

### Example Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## Error Responses

Standard error format:
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

Common status codes:
- `400`: Bad Request (validation error)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `429`: Too Many Requests (rate limit)
- `500`: Internal Server Error
