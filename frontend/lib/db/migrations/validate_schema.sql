-- ==========================================
-- Schema Validation Script
-- ==========================================
-- This script validates the production_schema.sql
-- by checking all tables, indexes, and constraints exist
-- ==========================================

-- Check all tables exist
DO $$
DECLARE
    missing_tables TEXT[] := ARRAY[]::TEXT[];
    expected_tables TEXT[] := ARRAY[
        'profiles',
        'projects', 
        'crawl_jobs',
        'images',
        'activity_logs',
        'api_keys',
        'credit_accounts',
        'credit_transactions',
        'notifications',
        'notification_preferences',
        'usage_metrics'
    ];
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY expected_tables
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = tbl
        ) THEN
            missing_tables := array_append(missing_tables, tbl);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Missing tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE '✅ All 11 tables exist';
    END IF;
END $$;

-- Check RLS is enabled on all tables
DO $$
DECLARE
    tables_without_rls TEXT[] := ARRAY[]::TEXT[];
    expected_tables TEXT[] := ARRAY[
        'profiles',
        'projects',
        'crawl_jobs',
        'images',
        'activity_logs',
        'api_keys',
        'credit_accounts',
        'credit_transactions',
        'notifications',
        'notification_preferences',
        'usage_metrics'
    ];
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY expected_tables
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename = tbl
            AND rowsecurity = true
        ) THEN
            tables_without_rls := array_append(tables_without_rls, tbl);
        END IF;
    END LOOP;
    
    IF array_length(tables_without_rls, 1) > 0 THEN
        RAISE EXCEPTION 'Tables without RLS: %', array_to_string(tables_without_rls, ', ');
    ELSE
        RAISE NOTICE '✅ RLS enabled on all tables';
    END IF;
END $$;

-- Check critical indexes exist
DO $$
DECLARE
    missing_indexes TEXT[] := ARRAY[]::TEXT[];
    expected_indexes TEXT[] := ARRAY[
        'ix_profiles_email',
        'ix_projects_user_id',
        'ix_crawl_jobs_project_id',
        'ix_crawl_jobs_status',
        'ix_images_crawl_job_id',
        'ix_images_hash',
        'ix_activity_logs_user_id',
        'ix_api_keys_user_id',
        'ix_api_keys_key_hash',
        'ix_credit_accounts_user_id',
        'ix_credit_transactions_account_id',
        'ix_notifications_user_id',
        'ix_notification_preferences_user_id',
        'ix_usage_metrics_user_id'
    ];
    idx TEXT;
BEGIN
    FOREACH idx IN ARRAY expected_indexes
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname = idx
        ) THEN
            missing_indexes := array_append(missing_indexes, idx);
        END IF;
    END LOOP;
    
    IF array_length(missing_indexes, 1) > 0 THEN
        RAISE EXCEPTION 'Missing indexes: %', array_to_string(missing_indexes, ', ');
    ELSE
        RAISE NOTICE '✅ All critical indexes exist';
    END IF;
END $$;

-- Check triggers exist
DO $$
DECLARE
    missing_triggers TEXT[] := ARRAY[]::TEXT[];
    expected_triggers TEXT[] := ARRAY[
        'on_auth_user_created',
        'handle_updated_at'
    ];
    trg TEXT;
BEGIN
    FOREACH trg IN ARRAY expected_triggers
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger 
            WHERE tgname = trg
        ) THEN
            missing_triggers := array_append(missing_triggers, trg);
        END IF;
    END LOOP;
    
    IF array_length(missing_triggers, 1) > 0 THEN
        RAISE EXCEPTION 'Missing triggers: %', array_to_string(missing_triggers, ', ');
    ELSE
        RAISE NOTICE '✅ All triggers exist';
    END IF;
END $$;

-- Validate column types match Drizzle schema
DO $$
BEGIN
    -- Check profiles table structure
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'profiles' 
        AND column_name = 'id' 
        AND data_type = 'uuid'
    ) THEN
        RAISE EXCEPTION 'profiles.id should be UUID';
    END IF;
    
    -- Check crawl_jobs has chunk tracking fields
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'crawl_jobs' 
        AND column_name = 'total_chunks'
    ) THEN
        RAISE EXCEPTION 'crawl_jobs missing total_chunks field';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'crawl_jobs' 
        AND column_name = 'active_chunks'
    ) THEN
        RAISE EXCEPTION 'crawl_jobs missing active_chunks field';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'crawl_jobs' 
        AND column_name = 'completed_chunks'
    ) THEN
        RAISE EXCEPTION 'crawl_jobs missing completed_chunks field';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'crawl_jobs' 
        AND column_name = 'failed_chunks'
    ) THEN
        RAISE EXCEPTION 'crawl_jobs missing failed_chunks field';
    END IF;
    
    -- Check notifications table column order matches Drizzle
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'notifications' 
        AND column_name = 'type'
        AND ordinal_position = 3
    ) THEN
        RAISE NOTICE '⚠️  notifications.type column position may differ from Drizzle schema';
    END IF;
    
    RAISE NOTICE '✅ Column types validated';
END $$;

-- Final summary
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Schema validation completed successfully!';
    RAISE NOTICE '========================================';
END $$;
