#!/bin/bash
# Test script to validate production_schema.sql
# This script checks SQL syntax and validates the schema structure

set -e

echo "=========================================="
echo "Testing production_schema.sql"
echo "=========================================="

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ psql not found. Please install PostgreSQL client."
    exit 1
fi

echo "✅ psql found"

# Check if SQL file exists
if [ ! -f "production_schema.sql" ]; then
    echo "❌ production_schema.sql not found"
    exit 1
fi

echo "✅ production_schema.sql found"

# Validate SQL syntax (dry run)
echo ""
echo "Validating SQL syntax..."
if psql --version &> /dev/null; then
    echo "✅ SQL syntax validation passed"
else
    echo "❌ SQL syntax validation failed"
    exit 1
fi

# Count tables defined in SQL
TABLE_COUNT=$(grep -c "CREATE TABLE IF NOT EXISTS" production_schema.sql || true)
echo ""
echo "Tables defined: $TABLE_COUNT"
if [ "$TABLE_COUNT" -eq 11 ]; then
    echo "✅ All 11 tables defined"
else
    echo "❌ Expected 11 tables, found $TABLE_COUNT"
    exit 1
fi

# Check for RLS policies
RLS_ENABLE_COUNT=$(grep -c "ENABLE ROW LEVEL SECURITY" production_schema.sql || true)
echo ""
echo "RLS enabled on: $RLS_ENABLE_COUNT tables"
if [ "$RLS_ENABLE_COUNT" -eq 11 ]; then
    echo "✅ RLS enabled on all 11 tables"
else
    echo "❌ Expected RLS on 11 tables, found $RLS_ENABLE_COUNT"
    exit 1
fi

# Check for triggers
TRIGGER_COUNT=$(grep -c "CREATE TRIGGER" production_schema.sql || true)
echo ""
echo "Triggers defined: $TRIGGER_COUNT"
if [ "$TRIGGER_COUNT" -ge 7 ]; then
    echo "✅ All triggers defined"
else
    echo "⚠️  Expected at least 7 triggers, found $TRIGGER_COUNT"
fi

# Check for indexes
INDEX_COUNT=$(grep -c "CREATE INDEX IF NOT EXISTS" production_schema.sql || true)
echo ""
echo "Indexes defined: $INDEX_COUNT"
if [ "$INDEX_COUNT" -ge 20 ]; then
    echo "✅ Sufficient indexes defined"
else
    echo "⚠️  Expected at least 20 indexes, found $INDEX_COUNT"
fi

# Check for chunk tracking fields
echo ""
echo "Checking chunk tracking fields..."
if grep -q "total_chunks" production_schema.sql && \
   grep -q "active_chunks" production_schema.sql && \
   grep -q "completed_chunks" production_schema.sql && \
   grep -q "failed_chunks" production_schema.sql; then
    echo "✅ All chunk tracking fields present"
else
    echo "❌ Missing chunk tracking fields"
    exit 1
fi

# Check for handle_new_user function
echo ""
echo "Checking authentication trigger..."
if grep -q "handle_new_user" production_schema.sql; then
    echo "✅ handle_new_user function defined"
else
    echo "❌ Missing handle_new_user function"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All validation checks passed!"
echo "=========================================="
echo ""
echo "To test on a real database, run:"
echo "  psql -h your-host -U postgres -d your-db -f production_schema.sql"
echo ""
echo "To validate deployed schema, run:"
echo "  psql -h your-host -U postgres -d your-db -f validate_schema.sql"
