"""
Tests for ImageRepository.

This module tests the ImageRepository methods including
validation result persistence.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.image_repository import ImageRepository
from backend.models import Image, CrawlJob, Project, Profile


@pytest.fixture
async def test_profile(session: AsyncSession):
    """Create a test profile."""
    from uuid import uuid4
    profile = Profile(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        role="user"
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


@pytest.fixture
async def test_project(session: AsyncSession, test_profile: Profile):
    """Create a test project."""
    project = Project(
        name="Test Project",
        user_id=test_profile.id,
        status="active"
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@pytest.fixture
async def test_crawl_job(session: AsyncSession, test_project: Project):
    """Create a test crawl job."""
    job = CrawlJob(
        project_id=test_project.id,
        name="Test Job",
        keywords=["test"],
        max_images=100,
        status="pending"
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


@pytest.fixture
async def test_image(session: AsyncSession, test_crawl_job: CrawlJob):
    """Create a test image."""
    image = Image(
        crawl_job_id=test_crawl_job.id,
        original_url="https://example.com/image.jpg",
        filename="test_image.jpg",
        is_valid=True,
        is_duplicate=False
    )
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


@pytest.fixture
def image_repository(session: AsyncSession):
    """Create an ImageRepository instance."""
    return ImageRepository(session)


class TestImageRepository:
    """Test suite for ImageRepository."""

    async def test_get_by_crawl_job(
        self,
        image_repository: ImageRepository,
        test_image: Image,
        test_crawl_job: CrawlJob
    ):
        """Test retrieving images by crawl job ID."""
        images = await image_repository.get_by_crawl_job(test_crawl_job.id)
        
        assert len(images) == 1
        assert images[0].id == test_image.id
        assert images[0].crawl_job_id == test_crawl_job.id

    async def test_count_by_job(
        self,
        image_repository: ImageRepository,
        test_image: Image,
        test_crawl_job: CrawlJob
    ):
        """Test counting images by job ID."""
        count = await image_repository.count_by_job(test_crawl_job.id)
        
        assert count == 1

    async def test_bulk_create(
        self,
        image_repository: ImageRepository,
        test_crawl_job: CrawlJob
    ):
        """Test bulk creating images."""
        images_data = [
            {
                "crawl_job_id": test_crawl_job.id,
                "original_url": f"https://example.com/image{i}.jpg",
                "filename": f"image{i}.jpg",
                "is_valid": True,
                "is_duplicate": False
            }
            for i in range(3)
        ]
        
        images = await image_repository.bulk_create(images_data)
        
        assert len(images) == 3
        for i, image in enumerate(images):
            assert image.crawl_job_id == test_crawl_job.id
            assert image.filename == f"image{i}.jpg"

    async def test_mark_validated_basic(
        self,
        image_repository: ImageRepository,
        test_image: Image
    ):
        """Test marking an image as validated with basic fields."""
        validation_result = {
            "is_valid": False,
            "is_duplicate": True
        }
        
        updated_image = await image_repository.mark_validated(
            test_image.id,
            validation_result
        )
        
        assert updated_image is not None
        assert updated_image.id == test_image.id
        assert updated_image.is_valid is False
        assert updated_image.is_duplicate is True

    async def test_mark_validated_with_metadata(
        self,
        image_repository: ImageRepository,
        test_image: Image
    ):
        """Test marking an image as validated with metadata."""
        validation_result = {
            "is_valid": True,
            "is_duplicate": False,
            "metadata": {
                "validation_score": 0.95,
                "validation_method": "perceptual_hash",
                "validated_at": "2025-12-03T12:00:00Z"
            }
        }
        
        updated_image = await image_repository.mark_validated(
            test_image.id,
            validation_result
        )
        
        assert updated_image is not None
        assert updated_image.is_valid is True
        assert updated_image.is_duplicate is False
        assert updated_image.metadata_ is not None
        assert updated_image.metadata_["validation_score"] == 0.95
        assert updated_image.metadata_["validation_method"] == "perceptual_hash"

    async def test_mark_validated_merges_metadata(
        self,
        session: AsyncSession,
        image_repository: ImageRepository,
        test_crawl_job: CrawlJob
    ):
        """Test that mark_validated merges metadata instead of replacing it."""
        # Create image with existing metadata
        image = Image(
            crawl_job_id=test_crawl_job.id,
            original_url="https://example.com/image.jpg",
            filename="test_image.jpg",
            is_valid=True,
            is_duplicate=False,
            metadata_={"existing_key": "existing_value"}
        )
        session.add(image)
        await session.commit()
        await session.refresh(image)
        
        # Update with validation metadata
        validation_result = {
            "is_valid": False,
            "is_duplicate": True,
            "metadata": {
                "validation_score": 0.85,
                "new_key": "new_value"
            }
        }
        
        updated_image = await image_repository.mark_validated(
            image.id,
            validation_result
        )
        
        assert updated_image is not None
        assert updated_image.is_valid is False
        assert updated_image.is_duplicate is True
        # Check that both old and new metadata exist
        assert updated_image.metadata_["existing_key"] == "existing_value"
        assert updated_image.metadata_["validation_score"] == 0.85
        assert updated_image.metadata_["new_key"] == "new_value"

    async def test_mark_validated_nonexistent_image(
        self,
        image_repository: ImageRepository
    ):
        """Test marking a nonexistent image as validated returns None."""
        validation_result = {
            "is_valid": False,
            "is_duplicate": True
        }
        
        result = await image_repository.mark_validated(
            999999,  # Non-existent ID
            validation_result
        )
        
        assert result is None
