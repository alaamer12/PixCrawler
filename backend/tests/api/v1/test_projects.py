"""
API integration tests for Projects endpoints.

Tests cover:
- List projects
- Create project
- Get project details
- Update project
- Delete project
- Response model validation
- OpenAPI schema generation
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import status

from backend.models import Project
from backend.services.project import ProjectService


@pytest.fixture
def mock_project_service():
    """Create mock project service."""
    return AsyncMock(spec=ProjectService)


@pytest.fixture
def mock_user():
    """Create mock authenticated user."""
    user_id = uuid4()
    return {
        "user_id": str(user_id),
        "email": "test@example.com",
        "profile": {"id": str(user_id), "email": "test@example.com"}
    }


@pytest.fixture
def sample_project(mock_user):
    """Create sample project for testing."""
    return Project(
        id=1,
        user_id=uuid.UUID(mock_user["user_id"]),
        name="Test Project",
        description="Test description",
        status="active",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        updated_at=datetime(2024, 1, 1, 10, 0, 0)
    )


@pytest.fixture
def override_dependencies(app, mock_project_service, mock_user):
    """Override FastAPI dependencies for testing."""
    from api.dependencies import get_project_service
    from backend.api.dependencies import get_current_user

    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield mock_project_service, mock_user

    app.dependency_overrides = {}


class TestListProjects:
    """Tests for GET /api/v1/projects endpoint."""

    def test_list_projects_success(self, client, override_dependencies, sample_project):
        """Test successful projects listing."""
        mock_service, mock_user = override_dependencies
        mock_service.get_projects.return_value = [sample_project]

        response = client.get("/api/v1/projects")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Test Project"

        # Verify service was called
        mock_service.get_projects.assert_called_once()

    def test_list_projects_empty(self, client, override_dependencies):
        """Test listing when no projects exist."""
        mock_service, mock_user = override_dependencies
        mock_service.get_projects.return_value = []

        response = client.get("/api/v1/projects")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 0

    def test_list_projects_response_model(self, client, override_dependencies, sample_project):
        """Test response model structure matches ProjectListResponse schema."""
        mock_service, mock_user = override_dependencies
        mock_service.get_projects.return_value = [sample_project]

        response = client.get("/api/v1/projects")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify structure
        assert "data" in data
        assert isinstance(data["data"], list)
        if len(data["data"]) > 0:
            required_fields = ["id", "name", "status", "created_at", "updated_at"]
            for field in required_fields:
                assert field in data["data"][0]

    def test_list_projects_unauthorized(self, client, app):
        """Test endpoint requires authentication."""
        response = client.get("/api/v1/projects")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestCreateProject:
    """Tests for POST /api/v1/projects endpoint."""

    def test_create_project_success(self, client, override_dependencies, sample_project):
        """Test successful project creation."""
        mock_service, mock_user = override_dependencies
        mock_service.create_project.return_value = sample_project

        project_data = {
            "name": "New Project",
            "description": "New description"
        }

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Project"

        # Verify service was called
        mock_service.create_project.assert_called_once()

    def test_create_project_validation(self, client, override_dependencies):
        """Test request validation."""
        # Missing required fields
        response = client.post("/api/v1/projects", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_project_response_model(self, client, override_dependencies, sample_project):
        """Test response model structure."""
        mock_service, mock_user = override_dependencies
        mock_service.create_project.return_value = sample_project

        project_data = {"name": "Test", "description": "Test"}

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify required fields
        required_fields = ["id", "name", "status", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data


class TestGetProject:
    """Tests for GET /api/v1/projects/{project_id} endpoint."""

    def test_get_project_success(self, client, override_dependencies, sample_project, mock_user):
        """Test successful project retrieval."""
        mock_service, user = override_dependencies
        mock_service.get_project.return_value = sample_project

        response = client.get("/api/v1/projects/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Project"

        # Verify service was called
        mock_service.get_project.assert_called_once()

    def test_get_project_not_found(self, client, override_dependencies):
        """Test project not found."""
        mock_service, mock_user = override_dependencies
        mock_service.get_project.return_value = None

        response = client.get("/api/v1/projects/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_project_response_model(self, client, override_dependencies, sample_project):
        """Test response model structure."""
        mock_service, mock_user = override_dependencies
        mock_service.get_project.return_value = sample_project

        response = client.get("/api/v1/projects/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required fields
        required_fields = ["id", "name", "status", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data


class TestUpdateProject:
    """Tests for PATCH /api/v1/projects/{project_id} endpoint."""

    def test_update_project_success(self, client, override_dependencies, sample_project):
        """Test successful project update."""
        mock_service, mock_user = override_dependencies
        updated_project = sample_project
        updated_project.name = "Updated Name"
        mock_service.update_project.return_value = updated_project

        update_data = {"name": "Updated Name"}

        response = client.patch("/api/v1/projects/1", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"

        # Verify service was called
        mock_service.update_project.assert_called_once()

    def test_update_project_not_found(self, client, override_dependencies):
        """Test updating non-existent project."""
        mock_service, mock_user = override_dependencies
        mock_service.update_project.return_value = None

        response = client.patch("/api/v1/projects/999", json={"name": "New Name"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_project_response_model(self, client, override_dependencies, sample_project):
        """Test response model structure."""
        mock_service, mock_user = override_dependencies
        mock_service.update_project.return_value = sample_project

        response = client.patch("/api/v1/projects/1", json={"name": "Updated"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required fields
        required_fields = ["id", "name", "status", "updated_at"]
        for field in required_fields:
            assert field in data


class TestDeleteProject:
    """Tests for DELETE /api/v1/projects/{project_id} endpoint."""

    def test_delete_project_success(self, client, override_dependencies):
        """Test successful project deletion."""
        mock_service, mock_user = override_dependencies
        mock_service.delete_project.return_value = True

        response = client.delete("/api/v1/projects/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data

        # Verify service was called
        mock_service.delete_project.assert_called_once()

    def test_delete_project_not_found(self, client, override_dependencies):
        """Test deleting non-existent project."""
        mock_service, mock_user = override_dependencies
        mock_service.delete_project.return_value = False

        response = client.delete("/api/v1/projects/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""

    def test_projects_endpoints_in_openapi(self, client):
        """Test that all project endpoints are documented."""
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check endpoints exist
        assert "/api/v1/projects/" in paths
        assert "/api/v1/projects/{project_id}" in paths

    def test_projects_endpoints_have_operation_ids(self, client):
        """Test that all endpoints have operation IDs."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check operation IDs
        assert paths["/api/v1/projects/"]["get"]["operationId"] == "listProjects"
        assert paths["/api/v1/projects/"]["post"]["operationId"] == "createProject"
        assert paths["/api/v1/projects/{project_id}"]["get"]["operationId"] == "getProject"
        assert paths["/api/v1/projects/{project_id}"]["patch"]["operationId"] == "updateProject"
        assert paths["/api/v1/projects/{project_id}"]["delete"]["operationId"] == "deleteProject"

    def test_projects_endpoints_have_response_models(self, client):
        """Test that all endpoints have response models defined."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Check response models exist
        assert "200" in paths["/api/v1/projects/"]["get"]["responses"]
        assert "201" in paths["/api/v1/projects/"]["post"]["responses"]
        assert "200" in paths["/api/v1/projects/{project_id}"]["get"]["responses"]
        assert "200" in paths["/api/v1/projects/{project_id}"]["patch"]["responses"]
        assert "200" in paths["/api/v1/projects/{project_id}"]["delete"]["responses"]


class TestIntegrationFlow:
    """Integration tests for complete project workflows."""

    def test_complete_project_workflow(self, client, override_dependencies, sample_project):
        """Test complete project workflow: create -> get -> update -> delete."""
        mock_service, mock_user = override_dependencies

        # Mock responses
        mock_service.create_project.return_value = sample_project
        mock_service.get_project.return_value = sample_project
        updated_project = sample_project
        updated_project.name = "Updated"
        mock_service.update_project.return_value = updated_project
        mock_service.delete_project.return_value = True

        # Step 1: Create project
        response1 = client.post("/api/v1/projects", json={"name": "Test", "description": "Test"})
        assert response1.status_code == status.HTTP_201_CREATED
        project = response1.json()
        project_id = project["id"]

        # Step 2: Get project
        response2 = client.get(f"/api/v1/projects/{project_id}")
        assert response2.status_code == status.HTTP_200_OK

        # Step 3: Update project
        response3 = client.patch(f"/api/v1/projects/{project_id}", json={"name": "Updated"})
        assert response3.status_code == status.HTTP_200_OK

        # Step 4: Delete project
        response4 = client.delete(f"/api/v1/projects/{project_id}")
        assert response4.status_code == status.HTTP_200_OK
