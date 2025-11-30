-- ==========================================
-- PixCrawler Database Schema - Production Ready
-- ==========================================
-- This script sets up the complete database schema with:
-- - All tables and relationships
-- - Row Level Security (RLS) policies
-- - Authentication triggers
-- - Indexes for performance
-- ==========================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- Core Models
-- ==========================================

-- Profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    onboarding_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS ix_profiles_role ON profiles(role);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects(status);

-- Crawl Jobs
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    keywords JSONB NOT NULL,
    max_images INTEGER NOT NULL DEFAULT 1000,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    total_images INTEGER NOT NULL DEFAULT 0,
    downloaded_images INTEGER NOT NULL DEFAULT 0,
    valid_images INTEGER NOT NULL DEFAULT 0,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    active_chunks INTEGER NOT NULL DEFAULT 0,
    completed_chunks INTEGER NOT NULL DEFAULT 0,
    failed_chunks INTEGER NOT NULL DEFAULT 0,
    task_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_crawl_jobs_project_id ON crawl_jobs(project_id);
CREATE INDEX IF NOT EXISTS ix_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX IF NOT EXISTS ix_crawl_jobs_project_status ON crawl_jobs(project_id, status);
CREATE INDEX IF NOT EXISTS ix_crawl_jobs_created_at ON crawl_jobs(created_at);

-- Images
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
    hash VARCHAR(64),
    is_valid BOOLEAN NOT NULL DEFAULT TRUE,
    is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
    labels JSONB,
    metadata JSONB,
    downloaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_images_crawl_job_id ON images(crawl_job_id);
CREATE INDEX IF NOT EXISTS ix_images_created_at ON images(created_at);
CREATE INDEX IF NOT EXISTS ix_images_hash ON images(hash);

-- Activity Logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(50),
    metadata JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_activity_logs_user_timestamp ON activity_logs(user_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_activity_logs_resource ON activity_logs(resource_type, resource_id);

-- ==========================================
-- API Keys
-- ==========================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    rate_limit INTEGER NOT NULL DEFAULT 1000,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    last_used_ip VARCHAR(45),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_api_keys_status_valid CHECK (status IN ('active', 'revoked', 'expired')),
    CONSTRAINT ck_api_keys_rate_limit_positive CHECK (rate_limit > 0),
    CONSTRAINT ck_api_keys_usage_count_positive CHECK (usage_count >= 0)
);

CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS ix_api_keys_status ON api_keys(status);

-- ==========================================
-- Credits & Billing
-- ==========================================

CREATE TABLE IF NOT EXISTS credit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    current_balance INTEGER NOT NULL DEFAULT 0,
    monthly_usage INTEGER NOT NULL DEFAULT 0,
    average_daily_usage NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    auto_refill_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    refill_threshold INTEGER NOT NULL DEFAULT 100,
    refill_amount INTEGER NOT NULL DEFAULT 500,
    monthly_limit INTEGER NOT NULL DEFAULT 2000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_credit_accounts_balance_positive CHECK (current_balance >= 0)
);

CREATE INDEX IF NOT EXISTS ix_credit_accounts_user_id ON credit_accounts(user_id);

CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES credit_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_credit_transactions_type_valid CHECK (type IN ('purchase', 'usage', 'refund', 'bonus'))
);

CREATE INDEX IF NOT EXISTS ix_credit_transactions_account_id ON credit_transactions(account_id);
CREATE INDEX IF NOT EXISTS ix_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_credit_transactions_created_at ON credit_transactions(created_at);

-- ==========================================
-- Notifications
-- ==========================================

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    icon VARCHAR(50),
    color VARCHAR(20),
    action_url TEXT,
    action_label VARCHAR(100),
    metadata JSONB,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_notifications_type_valid CHECK (type IN ('success', 'info', 'warning', 'error'))
);

CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = false;

CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    push_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    sms_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    crawl_jobs_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    datasets_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    billing_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    security_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    marketing_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    product_updates_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    digest_frequency VARCHAR(20) NOT NULL DEFAULT 'daily',
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_notification_preferences_user_id ON notification_preferences(user_id);

-- ==========================================
-- Usage & Metrics
-- ==========================================

CREATE TABLE IF NOT EXISTS usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    images_processed INTEGER NOT NULL DEFAULT 0,
    images_limit INTEGER NOT NULL DEFAULT 10000,
    storage_used_gb NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    storage_limit_gb NUMERIC(10, 2) NOT NULL DEFAULT 100.00,
    api_calls INTEGER NOT NULL DEFAULT 0,
    api_calls_limit INTEGER NOT NULL DEFAULT 50000,
    bandwidth_used_gb NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    bandwidth_limit_gb NUMERIC(10, 2) NOT NULL DEFAULT 500.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_usage_metrics_user_date UNIQUE (user_id, metric_date)
);

CREATE INDEX IF NOT EXISTS ix_usage_metrics_user_id ON usage_metrics(user_id);
CREATE INDEX IF NOT EXISTS ix_usage_metrics_metric_date ON usage_metrics(metric_date);

-- ==========================================
-- Row Level Security (RLS) Policies
-- ==========================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawl_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_metrics ENABLE ROW LEVEL SECURITY;

-- Profiles policies
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Projects policies
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own projects" ON projects;
CREATE POLICY "Users can create own projects" ON projects
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own projects" ON projects;
CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (auth.uid() = user_id);

-- Crawl Jobs policies (via projects)
DROP POLICY IF EXISTS "Users can view own crawl jobs" ON crawl_jobs;
CREATE POLICY "Users can view own crawl jobs" ON crawl_jobs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = crawl_jobs.project_id
            AND projects.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can create crawl jobs in own projects" ON crawl_jobs;
CREATE POLICY "Users can create crawl jobs in own projects" ON crawl_jobs
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = crawl_jobs.project_id
            AND projects.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can update own crawl jobs" ON crawl_jobs;
CREATE POLICY "Users can update own crawl jobs" ON crawl_jobs
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = crawl_jobs.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- Images policies (via crawl jobs)
DROP POLICY IF EXISTS "Users can view own images" ON images;
CREATE POLICY "Users can view own images" ON images
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM crawl_jobs
            JOIN projects ON projects.id = crawl_jobs.project_id
            WHERE crawl_jobs.id = images.crawl_job_id
            AND projects.user_id = auth.uid()
        )
    );

-- Activity Logs policies
DROP POLICY IF EXISTS "Users can view own activity logs" ON activity_logs;
CREATE POLICY "Users can view own activity logs" ON activity_logs
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own activity logs" ON activity_logs;
CREATE POLICY "Users can insert own activity logs" ON activity_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- API Keys policies
DROP POLICY IF EXISTS "Users can manage own API keys" ON api_keys;
CREATE POLICY "Users can manage own API keys" ON api_keys
    FOR ALL USING (auth.uid() = user_id);

-- Credit Accounts policies
DROP POLICY IF EXISTS "Users can view own credit account" ON credit_accounts;
CREATE POLICY "Users can view own credit account" ON credit_accounts
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own credit account" ON credit_accounts;
CREATE POLICY "Users can update own credit account" ON credit_accounts
    FOR UPDATE USING (auth.uid() = user_id);

-- Credit Transactions policies
DROP POLICY IF EXISTS "Users can view own transactions" ON credit_transactions;
CREATE POLICY "Users can view own transactions" ON credit_transactions
    FOR SELECT USING (auth.uid() = user_id);

-- Notifications policies
DROP POLICY IF EXISTS "Users can manage own notifications" ON notifications;
CREATE POLICY "Users can manage own notifications" ON notifications
    FOR ALL USING (auth.uid() = user_id);

-- Notification Preferences policies
DROP POLICY IF EXISTS "Users can manage own notification preferences" ON notification_preferences;
CREATE POLICY "Users can manage own notification preferences" ON notification_preferences
    FOR ALL USING (auth.uid() = user_id);

-- Usage Metrics policies
DROP POLICY IF EXISTS "Users can view own usage metrics" ON usage_metrics;
CREATE POLICY "Users can view own usage metrics" ON usage_metrics
    FOR SELECT USING (auth.uid() = user_id);

-- ==========================================
-- Triggers & Functions
-- ==========================================

-- Function to handle new user registration
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert profile
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
        COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture')
    );
    
    -- Create credit account with initial balance
    INSERT INTO public.credit_accounts (user_id, current_balance)
    VALUES (NEW.id, 100); -- 100 free credits for new users
    
    -- Create notification preferences with defaults
    INSERT INTO public.notification_preferences (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user registration
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to handle updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at on all relevant tables
DROP TRIGGER IF EXISTS handle_updated_at ON profiles;
CREATE TRIGGER handle_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS handle_updated_at ON projects;
CREATE TRIGGER handle_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS handle_updated_at ON crawl_jobs;
CREATE TRIGGER handle_updated_at
    BEFORE UPDATE ON crawl_jobs
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS handle_updated_at ON api_keys;
CREATE TRIGGER handle_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS handle_updated_at ON credit_accounts;
CREATE TRIGGER handle_updated_at
    BEFORE UPDATE ON credit_accounts
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS handle_updated_at ON notification_preferences;
CREATE TRIGGER handle_updated_at
    BEFORE UPDATE ON notification_preferences
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ==========================================
-- Completion Message
-- ==========================================

DO $$
BEGIN
    RAISE NOTICE '✅ Database schema deployed successfully!';
    RAISE NOTICE '✅ All tables created with proper relationships';
    RAISE NOTICE '✅ Row Level Security (RLS) enabled and configured';
    RAISE NOTICE '✅ Authentication triggers set up';
    RAISE NOTICE '✅ New users will automatically get:';
    RAISE NOTICE '   - Profile entry';
    RAISE NOTICE '   - Credit account with 100 free credits';
    RAISE NOTICE '   - Notification preferences';
END $$;
