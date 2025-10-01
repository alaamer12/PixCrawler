"""Image management endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Router with prefix
router = APIRouter(prefix="/images", tags=["Images"])


# Pydantic models
class Image(BaseModel):
    """Image model."""

    id: int = Field(..., example=1)
    url: str = Field(..., example="https://example.com/image.jpg")
    owner_id: int = Field(..., example=1)

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "url": "https://example.com/image.jpg",
                "owner_id": 1,
            }
        }


class ImageCreate(BaseModel):
    """Image creation model."""

    url: str = Field(..., example="https://example.com/image.jpg")
    owner_id: int = Field(..., example=1)


# Fake database
fake_images_db = [
    Image(id=1, url="https://picsum.photos/200/300", owner_id=1),
    Image(id=2, url="https://picsum.photos/300/400", owner_id=1),
    Image(id=3, url="https://picsum.photos/400/500", owner_id=2),
    Image(id=4, url="https://picsum.photos/500/600", owner_id=3),
]


@router.get("", response_model=List[Image], status_code=status.HTTP_200_OK)
async def get_images():
    """
    Retrieve all images.

    Returns a list of all images in the system.
    """
    return fake_images_db


@router.post("", response_model=Image, status_code=status.HTTP_201_CREATED)
async def create_image(image: ImageCreate):
    """
    Create a new image.

    Args:
        image: Image data for creation (url and owner_id)

    Returns:
        Created image with generated ID
    """
    # Generate new ID
    new_id = max(img.id for img in fake_images_db) + 1 if fake_images_db else 1

    # Create new image
    new_image = Image(id=new_id, url=image.url, owner_id=image.owner_id)

    # Add to fake database
    fake_images_db.append(new_image)

    return new_image


# Nested route for user images
@router.get(
    "/users/{user_id}/images",
    response_model=List[Image],
    status_code=status.HTTP_200_OK,
)
async def get_user_images(user_id: int):
    """
    Retrieve all images for a specific user.

    Args:
        user_id: The ID of the user whose images to retrieve

    Returns:
        List of images belonging to the user

    Raises:
        HTTPException: 404 if no images found for the user
    """
    user_images = [img for img in fake_images_db if img.owner_id == user_id]

    if not user_images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No images found for user with id {user_id}",
        )

    return user_images
