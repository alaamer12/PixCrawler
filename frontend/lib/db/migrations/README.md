# Database Schema Migrations

This directory contains the production-ready database schema and validation scripts for PixCrawler.

## Files

### production_schema.sql
The complete database schema for production deployment. This file is synchronized with the Drizzle schema defined in `frontend/lib/db/schema.ts`.

**Contents:**
- All 11 tables with proper relationships
- Row Level Security (RLS) policies for all tables
- Authentication triggers for new user registration
- Performance indexes
- Constraints and validations
- Auto-update triggers for `updated_at` fields

**Tables:**
1. `profiles` - User profiles (extends Supabase auth.users)
2. `projects` - Project organization
3. `crawl_jobs` - Image crawling tasks with chunk tracking
4. `images` - Crawled image metadata
5. `activity_logs` - User activity tracking
6. `api_keys` - Programmatic access keys
7. `credit_accounts` - User billing and credits
8. `credit_transactions` - Transaction history
9. `notifications` - User notifications
10. `notification_preferences` - Notification settings
11. `usage_metrics` - Daily usage tracking

### validate_schema.sql
Validation script to verify the schema is correctly deployed.

**Checks:**
- All 11 tables exist
- RLS is enabled on all tables
- Critical indexes are created
- Triggers are properly set up
- Column types match Drizzle schema
- Chunk tracking fields exist in crawl_jobs

## Usage

### Fresh Database Setup

To set up a fresh database with the production schema:

```bash
# Using psql
psql -h your-db-host -U postgres -d your-database -f production_schema.sql

# Using Supabase CLI
supabase db reset
supabase db push
```

### Validate Existing Database

To validate an existing database matches the schema:

```bash
# Using psql
psql -h your-db-host -U postgres -d your-database -f validate_schema.sql

# Expected output:
# NOTICE:  ✅ All 11 tables exist
# NOTICE:  ✅ RLS enabled on all tables
# NOTICE:  ✅ All critical indexes exist
# NOTICE:  ✅ All triggers exist
# NOTICE:  ✅ Column types validated
# NOTICE:  ✅ Schema validation completed successfully!
```

### Using Drizzle Migrations

For incremental schema changes during development:

```bash
# Generate migration from schema changes
bun run db:generate

# Apply migrations
bun run db:migrate

# Open Drizzle Studio to inspect database
bun run db:studio
```

## Schema Synchronization

**Single Source of Truth:** `frontend/lib/db/schema.ts` (Drizzle ORM)

The Drizzle schema is the authoritative definition. The production_schema.sql and backend SQLAlchemy models must be kept in sync with it.

### Synchronization Process

1. **Make changes in Drizzle schema** (`frontend/lib/db/schema.ts`)
2. **Generate Drizzle migration** (`bun run db:generate`)
3. **Update production_schema.sql** to match the changes
4. **Update backend SQLAlchemy models** (`backend/database/models.py`)
5. **Validate** using `validate_schema.sql`
6. **Test** on development database
7. **Review** with both frontend and backend teams

### Key Alignment Points

- **Table names:** Must match exactly (snake_case)
- **Column names:** Must match exactly (snake_case)
- **Data types:** Must be compatible (UUID, VARCHAR, INTEGER, JSONB, etc.)
- **Constraints:** Foreign keys, unique constraints, check constraints
- **Indexes:** Performance-critical indexes must exist
- **RLS Policies:** Must protect user data appropriately

## RLS Policies

All tables have Row Level Security enabled with policies that:

- **Profiles:** Users can view/update their own profile
- **Projects:** Users can manage their own projects
- **Crawl Jobs:** Users can manage jobs in their projects
- **Images:** Users can view images from their crawl jobs
- **Activity Logs:** Users can view their own activity
- **API Keys:** Users can manage their own API keys
- **Credit Accounts:** Users can view/update their own account
- **Credit Transactions:** Users can view their own transactions
- **Notifications:** Users can manage their own notifications
- **Notification Preferences:** Users can manage their own preferences
- **Usage Metrics:** Users can view their own metrics

## Triggers

### on_auth_user_created
Automatically creates related records when a new user signs up:
- Profile entry in `profiles` table
- Credit account with 100 free credits
- Notification preferences with defaults

### handle_updated_at
Automatically updates the `updated_at` timestamp on:
- profiles
- projects
- crawl_jobs
- api_keys
- credit_accounts
- notification_preferences

## Testing

### Manual Testing

1. **Create test user:**
```sql
-- This will trigger automatic profile, credit account, and preferences creation
INSERT INTO auth.users (id, email) 
VALUES (gen_random_uuid(), 'test@example.com');
```

2. **Verify RLS policies:**
```sql
-- Set user context
SET request.jwt.claim.sub = 'user-uuid-here';

-- Try to access data (should only see own data)
SELECT * FROM projects;
```

3. **Test triggers:**
```sql
-- Update a project
UPDATE projects SET name = 'New Name' WHERE id = 1;

-- Verify updated_at changed
SELECT updated_at FROM projects WHERE id = 1;
```

### Automated Testing

Run the validation script after any schema changes:

```bash
psql -f validate_schema.sql
```

## Troubleshooting

### Schema Drift Detected

If backend and frontend schemas don't match:

1. Check `backend/SCHEMA_ALIGNMENT_REVIEW.md` for documented differences
2. Review recent changes in `frontend/lib/db/schema.ts`
3. Update backend models in `backend/database/models.py`
4. Update `production_schema.sql` if needed
5. Run validation script

### Migration Conflicts

If Drizzle migrations conflict with production_schema.sql:

1. The Drizzle schema is the source of truth
2. Update production_schema.sql to match Drizzle
3. Regenerate migrations if needed
4. Test on development database first

### RLS Policy Issues

If users can't access their data:

1. Check RLS is enabled: `SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';`
2. Verify policies exist: `SELECT * FROM pg_policies WHERE schemaname = 'public';`
3. Check user authentication: `SELECT auth.uid();`
4. Review policy conditions in production_schema.sql

## Production Deployment

### Pre-Deployment Checklist

- [ ] Drizzle schema is up to date
- [ ] production_schema.sql matches Drizzle schema
- [ ] Backend models are synchronized
- [ ] Validation script passes on staging database
- [ ] RLS policies tested with real user accounts
- [ ] Triggers tested (new user creation, updated_at)
- [ ] Indexes verified for performance
- [ ] Backup of production database created

### Deployment Steps

1. **Backup production database**
2. **Test on staging environment**
3. **Apply schema changes during maintenance window**
4. **Run validation script**
5. **Monitor for errors**
6. **Verify application functionality**
7. **Rollback if issues detected**

## References

- [Drizzle ORM Documentation](https://orm.drizzle.team/)
- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Triggers](https://www.postgresql.org/docs/current/triggers.html)
- [ADR 001: Use Shared Supabase Database](../../../docs/001%20Use%20Shared%20Supabase%20Database.md)
