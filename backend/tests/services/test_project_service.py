"""
Unit tests for ProjectService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import HTTPException

from backend.models import Project
from backend.schemas.project import ProjectCreate, ProjectUpdate
from backend.services.project import ProjectService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def project_service(mock_repo):
    return ProjectService(mock_repo)


@pytest.mark.asyncio
async def test_get_projects(project_service, mock_repo):
    user_id = uuid4()
    mock_projects = [Project(id=1, user_id=user_id, name="Test Project")]
    mock_repo.get_by_user.return_value = mock_projects

    result = await project_service.get_projects(user_id)

    assert result == mock_projects
    mock_repo.get_by_user.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_project_success(project_service, mock_repo):
    user_id = uuid4()
    project_id = 1
    mock_project = Project(id=project_id, user_id=user_id, name="Test Project")
    mock_repo.get.return_value = mock_project

    result = await project_service.get_project(project_id, user_id)

    assert result == mock_project
    mock_repo.get.assert_called_once_with(project_id)


@pytest.mark.asyncio
async def test_get_project_not_found(project_service, mock_repo):
    user_id = uuid4()
    project_id = 1
    mock_repo.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await project_service.get_project(project_id, user_id)
    
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_project_forbidden(project_service, mock_repo):
    user_id = uuid4()
    other_user_id = uuid4()
    project_id = 1
    mock_project = Project(id=project_id, user_id=other_user_id, name="Test Project")
    mock_repo.get.return_value = mock_project

    with pytest.raises(HTTPException) as exc:
        await project_service.get_project(project_id, user_id)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_project(project_service, mock_repo):
    user_id = uuid4()
    project_in = ProjectCreate(name="New Project", description="Desc")
    mock_project = Project(id=1, user_id=user_id, name="New Project", description="Desc")
    mock_repo.create.return_value = mock_project

    result = await project_service.create_project(project_in, user_id)

    assert result == mock_project
    mock_repo.create.assert_called_once()
    call_args = mock_repo.create.call_args[0][0]
    assert call_args["name"] == "New Project"
    assert call_args["user_id"] == user_id


@pytest.mark.asyncio
async def test_update_project(project_service, mock_repo):
    user_id = uuid4()
    project_id = 1
    project_in = ProjectUpdate(name="Updated Name")
    mock_project = Project(id=project_id, user_id=user_id, name="Old Name")
    mock_repo.get.return_value = mock_project
    mock_repo.update.return_value = Project(id=project_id, user_id=user_id, name="Updated Name")

    result = await project_service.update_project(project_id, project_in, user_id)

    assert result.name == "Updated Name"
    mock_repo.update.assert_called_once_with(project_id, {"name": "Updated Name"})


@pytest.mark.asyncio
async def test_delete_project(project_service, mock_repo):
    user_id = uuid4()
    project_id = 1
    mock_project = Project(id=project_id, user_id=user_id, name="Test Project")
    mock_repo.get.return_value = mock_project
    mock_repo.delete.return_value = True

    result = await project_service.delete_project(project_id, user_id)

    assert result is True
    mock_repo.delete.assert_called_once_with(project_id)
