-- PixCrawler Database Schema
-- Complete SQL schema with chunks and user tiers
-- PostgreSQL 13+

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Profiles table (users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    user_tier VARCHAR(20) NOT NULL DEFAULT 'FREE' CHECK (user_tier IN ('FREE', 'PRO', 'ENTERPRISE')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_profiles_email ON profiles(email);
CREATE INDEX ix_profiles_user_tier ON profiles(user_tier);
CREATE INDEX ix_profiles_created_at ON profiles(created_at);


-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_projects_user_id ON projects(user_id);
CREATE INDEX ix_projects_status ON projects(status);
CREATE INDEX ix_projects_created_at ON projects(created_at);


-- Crawl Jobs table
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    keywords JSONB NOT NULL,
    max_images INTEGER NOT NULL DEFAULT 1000,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    total_images INTEGER NOT NULL DEFAULT 0,
    downloaded_images INTEGER NOT NULL DEFAULT 0,
    valid_images INTEGER NOT NULL DEFAULT 0,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    active_chunks INTEGER NOT NULL DEFAULT 0,
    completed_chunks INTEGER NOT NULL DEFAULT 0,
    failed_chunks INTEGER NOT NULL DEFAULT 0,
    task_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_crawl_jobs_project_id ON crawl_jobs(project_id);
CREATE INDEX ix_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX ix_crawl_jobs_created_at ON crawl_jobs(created_at);


-- ============================================================================
-- CHUNK TRACKING TABLE (NEW)
-- ============================================================================

-- Job Chunks table - Tracks individual processing chunks
CREATE TABLE IF NOT EXISTS job_chunks (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 0 AND priority <= 10),
    image_range JSONB NOT NULL,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    task_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for optimal query performance
CREATE INDEX ix_job_chunks_job_id ON job_chunks(job_id);
CREATE INDEX ix_job_chunks_status ON job_chunks(status);
CREATE INDEX ix_job_chunks_job_status ON job_chunks(job_id, status);
CREATE INDEX ix_job_chunks_priority_created ON job_chunks(priority, created_at);
CREATE INDEX ix_job_chunks_task_id ON job_chunks(task_id);
CREATE INDEX ix_job_chunks_created_at ON job_chunks(created_at);


-- ============================================================================
-- IMAGES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    crawl_job_id INTEGER NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    original_url TEXT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_url TEXT,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    format VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_images_crawl_job_id ON images(crawl_job_id);
CREATE INDEX ix_images_created_at ON images(created_at);


-- ============================================================================
-- ACTIVITY LOGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(50),
    metadata_ JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX ix_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX ix_activity_logs_resource ON activity_logs(resource_type, resource_id);


-- ============================================================================
-- CREDITS TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS credit_accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
    total_earned DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_spent DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_credit_accounts_user_id ON credit_accounts(user_id);


CREATE TABLE IF NOT EXISTS credit_transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES credit_accounts(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('earn', 'spend', 'refund', 'adjustment')),
    description TEXT,
    reference_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_credit_transactions_account_id ON credit_transactions(account_id);
CREATE INDEX ix_credit_transactions_created_at ON credit_transactions(created_at);


-- ============================================================================
-- NOTIFICATIONS TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE INDEX ix_notifications_read ON notifications(read);
CREATE INDEX ix_notifications_created_at ON notifications(created_at);


CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    email_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    push_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    sms_notifications BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);


-- ============================================================================
-- API KEYS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_api_keys_user_id ON api_keys(user_id);
CREATE INDEX ix_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX ix_api_keys_is_active ON api_keys(is_active);


-- ============================================================================
-- USAGE METRICS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS usage_metrics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(10, 2) NOT NULL DEFAULT 0,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_usage_metrics_user_id ON usage_metrics(user_id);
CREATE INDEX ix_usage_metrics_metric_type ON usage_metrics(metric_type);
CREATE INDEX ix_usage_metrics_period ON usage_metrics(period_start, period_end);


-- ============================================================================
-- FOREIGN KEY CONSTRAINTS SUMMARY
-- ============================================================================

/*
Relationships:
- profiles (1) -> (many) projects
- profiles (1) -> (many) activity_logs
- profiles (1) -> (many) credit_accounts
- profiles (1) -> (many) notifications
- profiles (1) -> (many) api_keys
- profiles (1) -> (many) usage_metrics
- projects (1) -> (many) crawl_jobs
- crawl_jobs (1) -> (many) job_chunks
- crawl_jobs (1) -> (many) images
- credit_accounts (1) -> (many) credit_transactions

All foreign keys use ON DELETE CASCADE for data consistency.
*/

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Job chunk progress summary
CREATE OR REPLACE VIEW job_chunk_progress AS
SELECT
    jc.job_id,
    COUNT(*) as total_chunks,
    SUM(CASE WHEN jc.status = 'completed' THEN 1 ELSE 0 END) as completed_chunks,
    SUM(CASE WHEN jc.status = 'failed' THEN 1 ELSE 0 END) as failed_chunks,
    SUM(CASE WHEN jc.status = 'processing' THEN 1 ELSE 0 END) as active_chunks,
    ROUND(
        100.0 * SUM(CASE WHEN jc.status = 'completed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) as completion_percentage
FROM job_chunks jc
GROUP BY jc.job_id;


-- View: User tier statistics
CREATE OR REPLACE VIEW user_tier_statistics AS
SELECT
    user_tier,
    COUNT(*) as user_count,
    COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as new_users_30d,
    COUNT(CASE WHEN updated_at > NOW() - INTERVAL '7 days' THEN 1 END) as active_users_7d
FROM profiles
GROUP BY user_tier;


-- View: Active crawl jobs with chunk status
CREATE OR REPLACE VIEW active_crawl_jobs_with_chunks AS
SELECT
    cj.id,
    cj.project_id,
    cj.name,
    cj.status,
    cj.progress,
    cj.total_chunks,
    cj.active_chunks,
    cj.completed_chunks,
    cj.failed_chunks,
    COUNT(jc.id) as actual_chunk_count,
    SUM(CASE WHEN jc.status = 'completed' THEN 1 ELSE 0 END) as actual_completed,
    SUM(CASE WHEN jc.status = 'failed' THEN 1 ELSE 0 END) as actual_failed
FROM crawl_jobs cj
LEFT JOIN job_chunks jc ON cj.id = jc.job_id
WHERE cj.status IN ('pending', 'processing')
GROUP BY cj.id, cj.project_id, cj.name, cj.status, cj.progress, cj.total_chunks, cj.active_chunks, cj.completed_chunks, cj.failed_chunks;
