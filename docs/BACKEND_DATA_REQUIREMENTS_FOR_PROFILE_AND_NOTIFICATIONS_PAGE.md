# Backend Requirements for Profile & Notifications

This document outlines the essential data structures and API endpoints required for functional Profile and Notifications pages.

---

## 1. User Profile

### Database Schema: `profiles`

```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  
  -- Basic Information
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  avatar_url TEXT,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  
  -- Professional Information
  bio TEXT,
  company VARCHAR(200),
  job_title VARCHAR(200),
  location VARCHAR(200),
  website TEXT,
  
  -- Social Links
  linkedin_username VARCHAR(100),
  github_username VARCHAR(100),
  twitter_username VARCHAR(100),
  
  -- Preferences
  timezone VARCHAR(100) DEFAULT 'UTC',
  language VARCHAR(10) DEFAULT 'en',
  public_profile BOOLEAN DEFAULT false,
  email_notifications BOOLEAN DEFAULT true,
  marketing_emails BOOLEAN DEFAULT false,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

**GET `/api/v1/profile`** - Retrieve user profile  
**PATCH `/api/v1/profile`** - Update profile fields  
**POST `/api/v1/profile/avatar`** - Upload avatar (multipart/form-data, max 5MB)  
**DELETE `/api/v1/account`** - Delete user account

---

## 2. Credits & Billing

### Database Schema

```sql
CREATE TABLE credit_accounts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  current_balance INTEGER NOT NULL DEFAULT 0,
  monthly_usage INTEGER DEFAULT 0,
  average_daily_usage DECIMAL(10,2) DEFAULT 0,
  
  -- Auto-refill
  auto_refill_enabled BOOLEAN DEFAULT false,
  refill_threshold INTEGER DEFAULT 100,
  refill_amount INTEGER DEFAULT 500,
  monthly_limit INTEGER DEFAULT 2000,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  type VARCHAR(20) NOT NULL, -- 'purchase', 'usage', 'refund', 'bonus'
  description TEXT NOT NULL,
  amount INTEGER NOT NULL,
  balance_after INTEGER NOT NULL,
  status VARCHAR(20) DEFAULT 'completed',
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

**GET `/api/v1/credits/balance`** - Current balance and auto-refill settings  
**GET `/api/v1/credits/transactions?limit=50&offset=0&type=purchase`** - Transaction history  
**GET `/api/v1/credits/usage-history?period=30d`** - Usage over time for charts  
**PATCH `/api/v1/credits/auto-refill`** - Update auto-refill settings  
**POST `/api/v1/credits/purchase`** - Purchase credits

---

## 3. Usage & Analytics

### Database Schema

```sql
CREATE TABLE usage_metrics (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  metric_date DATE NOT NULL,
  
  -- Metrics & Limits
  images_processed INTEGER DEFAULT 0,
  images_limit INTEGER DEFAULT 10000,
  storage_used_gb DECIMAL(10,2) DEFAULT 0,
  storage_limit_gb DECIMAL(10,2) DEFAULT 100,
  api_calls INTEGER DEFAULT 0,
  api_calls_limit INTEGER DEFAULT 50000,
  bandwidth_used_gb DECIMAL(10,2) DEFAULT 0,
  bandwidth_limit_gb DECIMAL(10,2) DEFAULT 500,
  
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, metric_date)
);
```

### API Endpoints

**GET `/api/v1/usage/metrics?period=30d`** - Current usage vs limits with trends  
**GET `/api/v1/usage/history?period=30d&metric=all`** - Historical data for charts

---

## 4. API Keys Management

### Database Schema

```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  name VARCHAR(200) NOT NULL,
  key_hash VARCHAR(255) NOT NULL,
  key_prefix VARCHAR(20) NOT NULL, -- e.g., 'pk_live_'
  status VARCHAR(20) DEFAULT 'active',
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

**GET `/api/v1/api-keys`** - List all keys (without full key value)  
**POST `/api/v1/api-keys`** - Create new key (returns full key once)  
**PATCH `/api/v1/api-keys/:id`** - Update name, permissions, or status  
**POST `/api/v1/api-keys/:id/regenerate`** - Generate new key (returns once)  
**DELETE `/api/v1/api-keys/:id`** - Delete key

---

## 5. Notifications System

### Database Schema

```sql
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  type VARCHAR(50) NOT NULL, -- 'success', 'info', 'warning', 'error'
  category VARCHAR(50), -- 'crawl_job', 'payment', 'system', 'security'
  icon VARCHAR(50), -- lucide icon name
  color VARCHAR(20),
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

**GET `/api/v1/notifications?unread=true&limit=50&offset=0`** - List notifications  
**GET `/api/v1/notifications/:id`** - Get single notification  
**PATCH `/api/v1/notifications/:id`** - Mark as read/unread  
**POST `/api/v1/notifications/mark-all-read`** - Mark all as read  
**DELETE `/api/v1/notifications/:id`** - Delete one  
**DELETE `/api/v1/notifications?read=true`** - Bulk delete

---

## 6. Notification Preferences

### Database Schema

```sql
CREATE TABLE notification_preferences (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) UNIQUE,
  
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

**GET `/api/v1/notifications/preferences`** - Get preferences  
**PATCH `/api/v1/notifications/preferences`** - Update preferences

---

## 7. User Settings

### Database Schema

```sql
CREATE TABLE user_settings (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) UNIQUE,
  
  -- Appearance
  theme VARCHAR(20) DEFAULT 'system', -- 'light', 'dark', 'system'
  compact_mode BOOLEAN DEFAULT false,
  
  -- Workspace
  default_view VARCHAR(20) DEFAULT 'grid',
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

**GET `/api/v1/settings`** - Get all settings  
**PATCH `/api/v1/settings`** - Update settings

---

## Authentication

All endpoints require:
- **Authorization**: `Bearer <jwt_token>` header
- **User Context**: Extracted from JWT
- **RLS**: Row-level security on all tables

## Error Format

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

**Status codes**: 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 429 (Rate Limit), 500 (Server Error)