"""
API integration tests for Projects.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.models import Project
from backend.services.project import ProjectService


@pytest.fixture
def mock_project_service():
    return AsyncMock(spec=ProjectService)


@pytest.fixture
def override_dependencies(app, mock_project_service):
    from backend.api.v1.endpoints.projects import get_project_service
    from backend.api.dependencies import get_current_user

    user_id = uuid4()
    mock_user = {
        "user_id": user_id,
        "email": "test@example.com",
        "profile": {"id": str(user_id), "email": "test@example.com"}
    }

    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    yield mock_project_service, user_id
    
    app.dependency_overrides = {}


def test_list_projects(client, override_dependencies):
    mock_service, user_id = override_dependencies
    mock_projects = [
        Project(
            id=1, 
            user_id=user_id, 
            name="Test Project", 
            description="Desc",
            status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
    ]
    mock_service.get_projects.return_value = mock_projects

    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "Test Project"
    mock_service.get_projects.assert_called_once_with(user_id)


def test_create_project(client, override_dependencies):
    mock_service, user_id = override_dependencies
    project_data = {"name": "New Project", "description": "Desc"}
    mock_project = Project(
        id=1, 
        user_id=user_id, 
        name="New Project", 
        description="Desc",
        status="active",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )
    mock_service.create_project.return_value = mock_project

    response = client.post("/api/v1/projects", json=project_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    mock_service.create_project.assert_called_once()


def test_get_project(client, override_dependencies):
    mock_service, user_id = override_dependencies
    mock_project = Project(
        id=1, 
        user_id=user_id, 
        name="Test Project",
        status="active",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )
    mock_service.get_project.return_value = mock_project

    response = client.get("/api/v1/projects/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    mock_service.get_project.assert_called_once_with(1, user_id)


def test_update_project(client, override_dependencies):
    mock_service, user_id = override_dependencies
    update_data = {"name": "Updated Name"}
    mock_project = Project(
        id=1, 
        user_id=user_id, 
        name="Updated Name",
        status="active",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )
    mock_service.update_project.return_value = mock_project

    response = client.patch("/api/v1/projects/1", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    mock_service.update_project.assert_called_once()


def test_delete_project(client, override_dependencies):
    mock_service, user_id = override_dependencies
    mock_service.delete_project.return_value = True

    response = client.delete("/api/v1/projects/1")

    assert response.status_code == 200
    mock_service.delete_project.assert_called_once_with(1, user_id)
