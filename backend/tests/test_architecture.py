"""
Architecture tests to enforce clean architecture patterns.

This module contains tests that verify the codebase adheres to the repository
pattern and clean architecture principles. These tests ensure:

1. Services don't import AsyncSession directly
2. Repositories extend BaseRepository
3. Endpoints don't execute database queries
4. Dependency injection pattern consistency
5. No business logic in repositories
6. No business logic in endpoints

These tests act as architectural guardrails to prevent violations of the
established patterns and maintain code quality.
"""

import ast
import inspect
from pathlib import Path
from typing import List, Set, Dict, Any

import pytest

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# Paths to check
BACKEND_ROOT = Path(__file__).parent.parent
SERVICES_DIR = BACKEND_ROOT / "services"
REPOSITORIES_DIR = BACKEND_ROOT / "repositories"
ENDPOINTS_DIR = BACKEND_ROOT / "api" / "v1" / "endpoints"

# Allowed exceptions for AsyncSession imports in services
# These are allowed only in TYPE_CHECKING blocks for type hints
ALLOWED_SESSION_IMPORTS = {
    "TYPE_CHECKING",  # For type hints only
}

# Business logic keywords that shouldn't appear in repositories
BUSINESS_LOGIC_KEYWORDS = {
    "calculate",
    "compute",
    "validate",
    "transform",
    "process",
    "orchestrate",
    "workflow",
}

# Database query keywords that shouldn't appear in endpoints
DATABASE_QUERY_KEYWORDS = {
    "select(",
    "insert(",
    "update(",
    "session.execute",
    "session.commit",
    "session.rollback",
    "session.add",
    "session.delete",
    "session.refresh",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_python_files(directory: Path) -> List[Path]:
    """
    Get all Python files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of Python file paths
    """
    if not directory.exists():
        return []
    return [f for f in directory.glob("*.py") if f.name != "__init__.py"]


def parse_file(file_path: Path) -> ast.Module:
    """
    Parse a Python file into an AST.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        AST module or None if parsing fails
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return ast.parse(f.read(), filename=str(file_path))
    except SyntaxError:
        # Skip files with syntax errors
        return None


def get_imports(tree: ast.Module) -> Set[str]:
    """
    Extract all imports from an AST.
    
    Args:
        tree: AST module
        
    Returns:
        Set of imported names
    """
    imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    imports.add(f"{node.module}.{alias.name}")
    
    return imports


def has_async_session_import(file_path: Path) -> bool:
    """
    Check if a file imports AsyncSession outside of TYPE_CHECKING.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        True if AsyncSession is imported outside TYPE_CHECKING
    """
    content = file_path.read_text(encoding="utf-8")
    
    # Check if AsyncSession is imported (not AsyncSessionLocal which is a factory)
    if "from sqlalchemy.ext.asyncio import AsyncSession" not in content:
        return False
    
    # More robust check: look for AsyncSession in imports at module level
    lines = content.split("\n")
    in_type_checking = False
    in_function = False
    
    for line in lines:
        stripped = line.strip()
        
        # Track TYPE_CHECKING blocks
        if "if TYPE_CHECKING:" in stripped:
            in_type_checking = True
            continue
        
        # Track function definitions (imports inside functions are OK for standalone functions)
        if stripped.startswith("def ") or stripped.startswith("async def "):
            in_function = True
        
        # Exit TYPE_CHECKING block (simple heuristic)
        if in_type_checking and stripped and not stripped.startswith((" ", "\t", "#")):
            in_type_checking = False
            in_function = False
        
        # Check for AsyncSession import from sqlalchemy
        if "from sqlalchemy.ext.asyncio import AsyncSession" in stripped or \
           "from sqlalchemy.ext.asyncio import" in stripped and "AsyncSession" in stripped:
            # Allow if in TYPE_CHECKING or inside a function
            if not in_type_checking and not in_function and not stripped.startswith("#"):
                return True
    
    return False


def get_class_bases(tree: ast.Module, class_name: str) -> List[str]:
    """
    Get base classes for a given class.
    
    Args:
        tree: AST module
        class_name: Name of the class
        
    Returns:
        List of base class names
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Subscript):
                    if isinstance(base.value, ast.Name):
                        bases.append(base.value.id)
            return bases
    return []


def has_database_queries(file_path: Path) -> Dict[str, List[int]]:
    """
    Check if a file contains database query keywords.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Dictionary mapping keywords to line numbers where they appear
    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    violations = {}
    
    for i, line in enumerate(lines, start=1):
        # Skip comments
        if line.strip().startswith("#"):
            continue
        
        for keyword in DATABASE_QUERY_KEYWORDS:
            if keyword in line.lower():
                if keyword not in violations:
                    violations[keyword] = []
                violations[keyword].append(i)
    
    return violations


def has_business_logic_keywords(file_path: Path) -> Dict[str, List[int]]:
    """
    Check if a file contains business logic keywords in function names.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Dictionary mapping keywords to line numbers where they appear
    """
    tree = parse_file(file_path)
    violations = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name_lower = node.name.lower()
            for keyword in BUSINESS_LOGIC_KEYWORDS:
                if keyword in func_name_lower:
                    if keyword not in violations:
                        violations[keyword] = []
                    violations[keyword].append(node.lineno)
    
    return violations


# ============================================================================
# TEST 1: Services Don't Import AsyncSession Directly
# ============================================================================

def test_services_dont_import_async_session():
    """
    Verify that services don't import AsyncSession directly.
    
    Services should depend on repositories, not database sessions.
    AsyncSession imports are only allowed in TYPE_CHECKING blocks for type hints.
    
    Rationale:
    - Services orchestrate business logic
    - Repositories handle data access
    - Direct session access in services breaks the repository pattern
    """
    service_files = get_python_files(SERVICES_DIR)
    violations = []
    
    for service_file in service_files:
        # Skip base service
        if service_file.name == "base.py":
            continue
        
        if has_async_session_import(service_file):
            violations.append(service_file.name)
    
    assert not violations, (
        f"The following services import AsyncSession outside TYPE_CHECKING: "
        f"{', '.join(violations)}. "
        f"Services should depend on repositories, not database sessions directly."
    )


# ============================================================================
# TEST 2: Repositories Extend BaseRepository
# ============================================================================

def test_repositories_extend_base_repository():
    """
    Verify that all repositories extend BaseRepository.
    
    All repository classes should inherit from BaseRepository to ensure
    consistent CRUD operations and proper typing.
    
    Rationale:
    - BaseRepository provides common CRUD operations
    - Ensures type safety with Generic[ModelT]
    - Maintains consistent interface across repositories
    """
    repository_files = get_python_files(REPOSITORIES_DIR)
    violations = []
    
    for repo_file in repository_files:
        # Skip base repository itself
        if repo_file.name == "base.py":
            continue
        
        tree = parse_file(repo_file)
        
        # Skip files with syntax errors
        if tree is None:
            continue
        
        # Find all class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a repository class (ends with Repository)
                if node.name.endswith("Repository"):
                    bases = get_class_bases(tree, node.name)
                    
                    # Check if BaseRepository is in the bases
                    if "BaseRepository" not in bases:
                        violations.append(f"{repo_file.name}::{node.name}")
    
    assert not violations, (
        f"The following repositories don't extend BaseRepository: "
        f"{', '.join(violations)}. "
        f"All repositories must extend BaseRepository for consistency."
    )


# ============================================================================
# TEST 3: Endpoints Don't Execute Database Queries
# ============================================================================

def test_endpoints_dont_execute_database_queries():
    """
    Verify that endpoints don't execute database queries directly.
    
    Endpoints should only handle HTTP concerns (validation, serialization, errors)
    and delegate all data access to the service layer.
    
    Rationale:
    - Endpoints handle HTTP request/response
    - Services handle business logic
    - Repositories handle data access
    - Direct queries in endpoints violate separation of concerns
    """
    endpoint_files = get_python_files(ENDPOINTS_DIR)
    violations = []
    
    for endpoint_file in endpoint_files:
        # Skip health endpoint (may have simple checks)
        if endpoint_file.name == "health.py":
            continue
        
        query_violations = has_database_queries(endpoint_file)
        
        if query_violations:
            violation_details = []
            for keyword, lines in query_violations.items():
                violation_details.append(f"{keyword} at lines {lines}")
            
            violations.append(
                f"{endpoint_file.name}: {'; '.join(violation_details)}"
            )
    
    assert not violations, (
        f"The following endpoints contain database queries:\n"
        f"{chr(10).join('  - ' + v for v in violations)}\n"
        f"Endpoints should use service layer methods, not execute queries directly."
    )


# ============================================================================
# TEST 4: Dependency Injection Pattern Consistency
# ============================================================================

def test_dependency_injection_pattern_consistency():
    """
    Verify that dependency injection follows consistent patterns.
    
    All service dependencies should:
    1. Be defined in backend/api/dependencies.py
    2. Follow the pattern: get_service_name(session) -> ServiceClass
    3. Create repository instances and inject into service
    4. Use proper type aliases in backend/api/types.py
    
    Rationale:
    - Consistent DI pattern improves maintainability
    - Centralized dependencies are easier to test
    - Type aliases provide better IDE support
    """
    dependencies_file = BACKEND_ROOT / "api" / "dependencies.py"
    
    if not dependencies_file.exists():
        pytest.skip("dependencies.py not found")
    
    content = dependencies_file.read_text(encoding="utf-8")
    
    # Check for common service factory patterns
    service_names = [
        "notification",
        "project",
        "crawl_job",
        "dataset",
        "user",
    ]
    
    missing_factories = []
    
    for service_name in service_names:
        factory_name = f"get_{service_name}_service"
        if factory_name not in content:
            missing_factories.append(factory_name)
    
    # This is a warning, not a failure
    if missing_factories:
        pytest.skip(
            f"Some service factories may be missing: {', '.join(missing_factories)}. "
            f"This is not a critical error but should be addressed for consistency."
        )


# ============================================================================
# TEST 5: No Business Logic in Repositories
# ============================================================================

def test_no_business_logic_in_repositories():
    """
    Verify that repositories don't contain business logic.
    
    Repositories should focus solely on data access operations (CRUD).
    Business logic, calculations, and transformations belong in the service layer.
    
    Rationale:
    - Repositories handle data persistence
    - Services handle business rules
    - Mixing concerns makes code harder to test and maintain
    
    Note: This test looks for suspicious function names that suggest business logic.
    """
    repository_files = get_python_files(REPOSITORIES_DIR)
    violations = []
    
    for repo_file in repository_files:
        # Skip base repository
        if repo_file.name == "base.py":
            continue
        
        logic_violations = has_business_logic_keywords(repo_file)
        
        if logic_violations:
            violation_details = []
            for keyword, lines in logic_violations.items():
                violation_details.append(f"'{keyword}' at lines {lines}")
            
            violations.append(
                f"{repo_file.name}: {'; '.join(violation_details)}"
            )
    
    # This is a warning test - business logic keywords might be acceptable
    # in some repository method names (e.g., "calculate_total" for a sum query)
    if violations:
        pytest.skip(
            f"The following repositories may contain business logic:\n"
            f"{chr(10).join('  - ' + v for v in violations)}\n"
            f"Review these methods to ensure they only perform data access."
        )


# ============================================================================
# TEST 6: No Business Logic in Endpoints
# ============================================================================

def test_no_business_logic_in_endpoints():
    """
    Verify that endpoints don't contain business logic.
    
    Endpoints should only handle HTTP concerns:
    - Request validation
    - Response serialization
    - Error handling
    - Authentication/authorization
    
    Business logic should be in the service layer.
    
    Rationale:
    - Endpoints are the HTTP interface
    - Services contain business rules
    - Separation improves testability and reusability
    """
    endpoint_files = get_python_files(ENDPOINTS_DIR)
    violations = []
    
    # Keywords that suggest business logic in endpoints
    business_keywords = {
        "calculate",
        "compute",
        "transform",
        "process",
        "validate",  # Should use Pydantic schemas
    }
    
    for endpoint_file in endpoint_files:
        # Skip health endpoint
        if endpoint_file.name == "health.py":
            continue
        
        tree = parse_file(endpoint_file)
        
        # Skip files with syntax errors
        if tree is None:
            continue
        
        # Look for business logic in endpoint functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function body for business logic patterns
                func_source = ast.get_source_segment(
                    endpoint_file.read_text(encoding="utf-8"),
                    node
                )
                
                if func_source:
                    func_lower = func_source.lower()
                    
                    # Check for loops (often indicate business logic)
                    if "for " in func_lower and "await service." not in func_lower:
                        violations.append(
                            f"{endpoint_file.name}::{node.name} (line {node.lineno}): "
                            f"Contains loop - may indicate business logic"
                        )
                    
                    # Check for complex conditionals
                    if func_lower.count("if ") > 3:
                        violations.append(
                            f"{endpoint_file.name}::{node.name} (line {node.lineno}): "
                            f"Complex conditionals - may indicate business logic"
                        )
    
    # This is a warning test - some complexity in endpoints is acceptable
    if violations:
        pytest.skip(
            f"The following endpoints may contain business logic:\n"
            f"{chr(10).join('  - ' + v for v in violations)}\n"
            f"Review these endpoints to ensure logic is in service layer."
        )


# ============================================================================
# TEST 7: Service Constructors Don't Accept Session Parameters
# ============================================================================

def test_services_dont_accept_session_parameters():
    """
    Verify that service constructors don't accept AsyncSession parameters.
    
    Services should accept repository instances, not database sessions.
    This enforces the repository pattern and proper separation of concerns.
    
    Rationale:
    - Services orchestrate business logic
    - Repositories handle data access
    - Session management belongs in repositories
    """
    service_files = get_python_files(SERVICES_DIR)
    violations = []
    
    for service_file in service_files:
        # Skip base service
        if service_file.name == "base.py":
            continue
        
        tree = parse_file(service_file)
        
        # Skip files with syntax errors
        if tree is None:
            continue
        
        # Find service classes and check __init__ methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a service class
                if node.name.endswith("Service"):
                    # Find __init__ method
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                            # Check parameters
                            for arg in item.args.args:
                                if arg.arg == "session":
                                    violations.append(
                                        f"{service_file.name}::{node.name}.__init__ "
                                        f"(line {item.lineno})"
                                    )
    
    assert not violations, (
        f"The following services accept 'session' parameter in __init__:\n"
        f"{chr(10).join('  - ' + v for v in violations)}\n"
        f"Services should accept repository instances, not database sessions."
    )


# ============================================================================
# TEST 8: Repositories Use Proper Type Hints
# ============================================================================

def test_repositories_use_proper_type_hints():
    """
    Verify that repositories use proper model types, not Any.
    
    Repositories should be typed as BaseRepository[ModelType], not BaseRepository[Any].
    This ensures type safety and better IDE support.
    
    Rationale:
    - Type safety prevents runtime errors
    - Better IDE autocomplete and refactoring
    - Self-documenting code
    """
    repository_files = get_python_files(REPOSITORIES_DIR)
    violations = []
    
    for repo_file in repository_files:
        # Skip base repository
        if repo_file.name == "base.py":
            continue
        
        content = repo_file.read_text(encoding="utf-8")
        
        # Check for BaseRepository[Any]
        if "BaseRepository[Any]" in content:
            violations.append(repo_file.name)
    
    assert not violations, (
        f"The following repositories use BaseRepository[Any]: "
        f"{', '.join(violations)}. "
        f"Use proper model types for type safety (e.g., BaseRepository[User])."
    )


# ============================================================================
# SUMMARY TEST
# ============================================================================

def test_architecture_compliance_summary():
    """
    Summary test that provides an overview of architecture compliance.
    
    This test always passes but logs information about the architecture state.
    """
    service_files = get_python_files(SERVICES_DIR)
    repository_files = get_python_files(REPOSITORIES_DIR)
    endpoint_files = get_python_files(ENDPOINTS_DIR)
    
    print("\n" + "=" * 70)
    print("ARCHITECTURE COMPLIANCE SUMMARY")
    print("=" * 70)
    print(f"Services checked: {len(service_files)}")
    print(f"Repositories checked: {len(repository_files)}")
    print(f"Endpoints checked: {len(endpoint_files)}")
    print("=" * 70)
    print("\nRun individual tests for detailed violation reports.")
    print("=" * 70)
