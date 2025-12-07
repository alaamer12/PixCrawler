"""
Test script for login endpoint.

This script demonstrates how to use the login endpoint and make authenticated requests.

Usage:
    python backend/examples/test_login.py
"""

import requests
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "user@example.com"
TEST_PASSWORD = "YourPassword123!"


class PixCrawlerClient:
    """Simple client for PixCrawler API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def login(self, email: str, password: str) -> dict:
        """
        Login and store tokens.

        Args:
            email: User email
            password: User password

        Returns:
            Token response with access_token, refresh_token, etc.

        Raises:
            requests.HTTPError: If login fails
        """
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

        print(f"✅ Login successful!")
        print(f"   Token type: {data['token_type']}")
        print(f"   Expires in: {data['expires_in']} seconds")
        print(f"   Access token: {self.access_token[:50]}...")

        return data

    def get_headers(self) -> dict:
        """Get authorization headers."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_profile(self) -> dict:
        """Get current user profile."""
        response = requests.get(
            f"{self.base_url}/api/v1/auth/me",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def list_projects(self) -> dict:
        """List user projects."""
        response = requests.get(
            f"{self.base_url}/api/v1/projects",
            headers=self.get_headers()
        )
        response.raise_for_status()
        return response.json()

    def create_project(self, name: str, description: str = "") -> dict:
        """Create a new project."""
        response = requests.post(
            f"{self.base_url}/api/v1/projects",
            headers=self.get_headers(),
            json={"name": name, "description": description}
        )
        response.raise_for_status()
        return response.json()


def main():
    """Run login test."""
    print("=" * 60)
    print("PixCrawler Login Test")
    print("=" * 60)
    print()

    # Create client
    client = PixCrawlerClient()

    try:
        # Step 1: Login
        print("Step 1: Login")
        print(f"   Email: {TEST_EMAIL}")
        print(f"   Password: {'*' * len(TEST_PASSWORD)}")
        print()

        client.login(TEST_EMAIL, TEST_PASSWORD)
        print()

        # Step 2: Get profile
        print("Step 2: Get user profile")
        profile = client.get_profile()
        print(f"✅ Profile retrieved:")
        print(f"   ID: {profile['id']}")
        print(f"   Email: {profile['email']}")
        print(f"   Name: {profile['full_name']}")
        print(f"   Active: {profile['is_active']}")
        print()

        # Step 3: List projects
        print("Step 3: List projects")
        projects = client.list_projects()
        print(f"✅ Projects retrieved:")
        print(f"   Total: {projects['meta']['total']}")
        if projects['data']:
            for project in projects['data']:
                print(f"   - {project['name']}: {project['description']}")
        else:
            print("   (No projects yet)")
        print()

        # Step 4: Create a test project
        print("Step 4: Create test project")
        new_project = client.create_project(
            name="Test Project",
            description="Created via login test script"
        )
        print(f"✅ Project created:")
        print(f"   ID: {new_project['id']}")
        print(f"   Name: {new_project['name']}")
        print(f"   Description: {new_project['description']}")
        print()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except requests.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
