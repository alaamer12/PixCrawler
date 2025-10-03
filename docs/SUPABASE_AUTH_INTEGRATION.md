# Supabase Auth Integration Guide

## Overview

The PixCrawler backend has been updated to integrate with Supabase Auth instead of implementing custom JWT authentication. This provides a more robust, secure, and maintainable authentication system.

## Architecture Changes

### Before (Custom Auth)
```
Frontend → Custom JWT Auth → Backend API → Database
```

### After (Supabase Auth Integration)
```
Frontend → Supabase Auth → Backend API → Supabase Database
```

## Key Components

### 1. Supabase Auth Service (`backend/services/supabase_auth.py`)
- Handles Supabase JWT token verification
- Manages user profile synchronization
- Provides user context for API endpoints

### 2. Authentication Dependencies (`backend/api/dependencies.py`)
- `get_current_user`: Required authentication dependency
- `get_current_user_optional`: Optional authentication dependency
- `get_supabase_auth_service`: Service dependency injection

### 3. Updated Auth Endpoints (`backend/api/v1/endpoints/auth.py`)
- `GET /auth/me`: Get current user profile
- `POST /auth/verify-token`: Verify Supabase JWT token
- `POST /auth/sync-profile`: Sync user profile from Supabase Auth

## Configuration

### Environment Variables
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Database (same Supabase database)
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

### Dependencies
```toml
dependencies = [
    "supabase>=2.0.0",
    "PyJWT>=2.8.0",
    # ... other dependencies
]
```

## Authentication Flow

### 1. Frontend Authentication
```typescript
// User signs in through Supabase Auth (frontend)
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get JWT token
const token = data.session?.access_token
```

### 2. Backend API Calls
```typescript
// Include token in API requests
const response = await fetch('/api/v1/datasets/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

### 3. Backend Token Verification
```python
# Automatic token verification in endpoints
@router.get("/datasets/")
async def list_datasets(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # current_user contains verified user information
    user_id = current_user["user_id"]
    profile = current_user["profile"]
    # ... endpoint logic
```

## Database Schema

The backend works with your existing database schema:

```sql
-- Profiles table (extends Supabase auth.users)
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email VARCHAR(255) NOT NULL UNIQUE,
  full_name VARCHAR(100),
  avatar_url TEXT,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Your existing tables (projects, crawl_jobs, images, etc.)
-- Reference profiles.id for user relationships
```

## API Endpoints

### Authentication Endpoints
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/verify-token` - Verify token validity
- `POST /api/v1/auth/sync-profile` - Sync user profile

### Protected Endpoints
All dataset and user management endpoints now require Supabase authentication:
- `POST /api/v1/datasets/` - Create dataset (requires auth)
- `GET /api/v1/datasets/` - List user's datasets (requires auth)
- `GET /api/v1/datasets/{id}` - Get dataset (requires auth + ownership)

## Benefits

### 1. Security
- ✅ Industry-standard JWT tokens
- ✅ Built-in rate limiting
- ✅ Email verification
- ✅ Password reset functionality
- ✅ Multi-factor authentication support

### 2. Maintenance
- ✅ No custom auth code to maintain
- ✅ Automatic security updates
- ✅ Consistent auth across frontend/backend
- ✅ Built-in user management

### 3. Features
- ✅ Social login providers
- ✅ Row Level Security (RLS)
- ✅ Real-time subscriptions
- ✅ User metadata management

## Migration Steps

### 1. Update Environment Variables
```bash
# Remove old JWT settings
# SECRET_KEY=...
# ACCESS_TOKEN_EXPIRE_MINUTES=...

# Add Supabase settings
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

### 2. Install Dependencies
```bash
uv add supabase PyJWT
```

### 3. Update Frontend API Calls
```typescript
// Use Supabase session token for API calls
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token

// Include in API requests
fetch('/api/v1/datasets/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### 4. Test Authentication
```bash
# Start backend
uv run pixcrawler-api

# Test endpoints
curl -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
     http://localhost:8000/api/v1/auth/me
```

## Removed Components

The following custom auth components have been removed/replaced:

- ❌ `backend/services/auth.py` (custom JWT auth)
- ❌ Custom password hashing
- ❌ Custom token generation/verification
- ❌ Login/logout endpoints (handled by Supabase)

## Error Handling

The system provides comprehensive error handling:

```python
# Invalid/expired token
# HTTP 401 Unauthorized
e = {
  "error": {
    "type": "AuthenticationError",
    "message": "Invalid or expired token"
  }
}

# Missing token
# HTTP 401 Unauthorized
e2 = {
  "error": {
    "type": "HTTPException", 
    "message": "Authentication required"
  }
}
```

## Testing

```python
# Test with valid Supabase token
def test_protected_endpoint():
    token = "valid_supabase_jwt_token"
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

This integration provides a more robust, secure, and maintainable authentication system while leveraging your existing Supabase infrastructure.
