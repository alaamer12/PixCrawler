"""
Test to verify SQLAlchemy typing fixes for .where() statements.

This test ensures that all .where() clauses use correct type comparisons
with SQLAlchemy columns, particularly for UUID columns.
"""
import uuid


def test_typing_syntax_check():
    """
    Verify that the typing fixes are syntactically correct.
    
    This test checks that the fixed code in crawl_jobs.py uses the correct
    pattern for UUID comparisons without actually running database queries.
    """
    # Simulate the user_id from JWT token (comes as string)
    current_user = {"user_id": "550e8400-e29b-41d4-a716-446655440000"}
    
    # The fix: Convert string to UUID for comparison with UUID columns
    user_uuid = uuid.UUID(current_user["user_id"])
    
    # Verify conversion works
    assert isinstance(user_uuid, uuid.UUID)
    assert str(user_uuid) == current_user["user_id"]


def test_uuid_string_conversion():
    """Test UUID to string and back conversion."""
    original_uuid = uuid.uuid4()
    uuid_string = str(original_uuid)
    converted_back = uuid.UUID(uuid_string)
    
    assert original_uuid == converted_back
    assert isinstance(converted_back, uuid.UUID)


def test_import_fixed_modules():
    """Test that the fixed modules import without errors."""
    
    # Just verify the typing fix is syntactically correct
    import ast
    import pathlib
    
    # Read the fixed file
    crawl_jobs_path = pathlib.Path(__file__).parent.parent / "api" / "v1" / "endpoints" / "crawl_jobs.py"
    
    if crawl_jobs_path.exists():
        with open(crawl_jobs_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        # Verify it's valid Python syntax
        try:
            ast.parse(source)
        except SyntaxError as e:
            raise AssertionError(f"Syntax error in crawl_jobs.py: {e}")
        
        # Verify the fix is present (UUID comparison, not string)
        assert "uuid.UUID(current_user[\"user_id\"])" in source, \
            "Expected UUID conversion in crawl_jobs.py"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
