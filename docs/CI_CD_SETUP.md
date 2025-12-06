# CI/CD Setup Documentation

## GitHub Secrets Configuration

To enable CI/CD tests with PostgreSQL and Supabase, configure the following GitHub Secrets in your repository:

### Required Secrets

Navigate to: **Repository Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | Example/Notes |
|-------------|-------------|---------------|
| `TEST_POSTGRES_PASSWORD` | PostgreSQL password for CI tests | Any secure password (e.g., `ci_test_password_123`) |
| `TEST_SUPABASE_URL` | Supabase project URL for testing | `https://your-test-project.supabase.co` |
| `TEST_SUPABASE_SERVICE_KEY` | Supabase service role key | From Supabase Dashboard → Project Settings → API |
| `TEST_SUPABASE_ANON_KEY` | Supabase anonymous key | From Supabase Dashboard → Project Settings → API |

### Optional (Uses Defaults if Not Set)

The workflow includes fallback values for all secrets, so tests will run even without secrets (using placeholder values). However, for production-quality testing, it's recommended to set real Supabase credentials.

---

## Local Development Setup

### Quick Start

1. **Copy the template:**
   ```bash
   cp .env.test.example .env.test
   ```

2. **Update `.env.test` with your local values:**
   - Update `DATABASE_URL` to point to your local PostgreSQL
   - Update `SUPABASE_*` credentials (or use test/staging project)
   - Update `REDIS_URL` if using different Redis instance

3. **Run tests:**
   ```bash
   python -m pytest --tb=short -q
   ```

### Local PostgreSQL Setup

#### Using Docker (Recommended)
```bash
docker run -d \
  --name pixcrawler-test-db \
  -e POSTGRES_DB=pixcrawler_test \
  -e POSTGRES_USER=test_user \
  -e POSTGRES_PASSWORD=test_password \
  -p 5432:5432 \
  postgres:15-alpine
```

#### Using System PostgreSQL
```sql
CREATE DATABASE pixcrawler_test;
CREATE USER test_user WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE pixcrawler_test TO test_user;
```

Then update `.env.test`:
```bash
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/pixcrawler_test
```

### Local Redis Setup

#### Using Docker (Recommended)
```bash
docker run -d \
  --name pixcrawler-test-redis \
  -p 6379:6379 \
  redis:latest
```

#### Using System Redis
Install Redis and start the service, then update `.env.test`:
```bash
REDIS_URL=redis://localhost:6379/0
```

---

## CI/CD Workflow Overview

The GitHub Actions workflow now includes:

1. **PostgreSQL Service** - Runs `postgres:15-alpine` with health checks
2. **Redis Service** - Runs `redis:latest` with health checks
3. **Dynamic .env.test Creation** - Populates from GitHub Secrets
4. **Automated Testing** - Runs full test suite with coverage

### Workflow Steps

```yaml
1. Checkout code
2. Install UV package manager
3. Setup Python (matrix: 3.11, 3.12, 3.13, 3.14)
4. Install dependencies
5. Setup test environment (.env.test creation) ← NEW
6. Run pre-commit hooks
7. Run tests
8. Upload coverage
```

---

## Troubleshooting

### Tests Fail with Database Connection Error

**Symptom:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
- Ensure PostgreSQL is running locally or in Docker
- Verify `DATABASE_URL` in `.env.test` is correct
- Check PostgreSQL is listening on the correct port (default: 5432)

### Tests Fail with Supabase Auth Error

**Symptom:** `Invalid API key` or `Authentication failed`

**Solutions:**
- Verify Supabase credentials in `.env.test` are correct
- Use a test/staging Supabase project (not production)
- Minimum 50 characters required for keys (validation requirement)

### CI/CD Workflow Fails

**Symptom:** GitHub Actions job fails

**Solutions:**
- Check GitHub Secrets are configured correctly
- Review workflow logs for specific error messages
- Ensure services started successfully (check health checks)

---

## Security Best Practices

⚠️ **NEVER commit `.env.test` to version control**

✅ **DO:**
- Use `.env.test.example` as a template
- Store real credentials in GitHub Secrets
- Use separate test/staging Supabase projects
- Rotate credentials regularly

❌ **DON'T:**
- Commit `.env.test` file
- Use production credentials in tests
- Share `.env.test` with sensitive data
- Hardcode credentials in workflow files
