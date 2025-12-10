-- PixCrawler: Drop all tables and start fresh
-- WARNING: This will delete ALL data in the database!

-- Drop all tables in reverse dependency order
DROP TABLE IF EXISTS policy_execution_logs CASCADE;
DROP TABLE IF EXISTS archival_policies CASCADE;
DROP TABLE IF EXISTS retention_policies CASCADE;
DROP TABLE IF EXISTS job_chunks CASCADE;
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS images CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;
DROP TABLE IF EXISTS crawl_jobs CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS usage_metrics CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS notification_preferences CASCADE;
DROP TABLE IF EXISTS credit_accounts CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;

-- Drop Alembic version table
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Confirm clean slate
SELECT 'All tables dropped successfully!' as status;
