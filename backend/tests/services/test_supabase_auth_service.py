"""
Tests for Supabase authentication service.
"""
import pytest
from datetime import datetime, timedelta
from backend.services.supabase_auth import SupabaseAuthService
from backend.core.exceptions import RateLimitExceeded

class TestSupabaseAuthServiceTierLimits:
    """Test tier limits and validation in SupabaseAuthService."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.service = SupabaseAuthService()
        self.user_id = "test_user_123"
        self.now = datetime.utcnow()
        
    def test_get_tier_limits_free(self):
        """Test getting limits for FREE tier."""
        limits = self.service._get_tier_limits("FREE")
        assert limits["max_concurrent_jobs"] == 1
        assert limits["max_images_per_job"] == 100
        assert limits["max_jobs_per_day"] == 3
        assert limits["max_projects"] == 3
        assert limits["max_team_members"] == 1
    
    def test_get_tier_limits_pro(self):
        """Test getting limits for PRO tier."""
        limits = self.service._get_tier_limits("PRO")
        assert limits["max_concurrent_jobs"] == 3
        assert limits["max_images_per_job"] == 1000
        assert limits["max_jobs_per_day"] == 20
        assert limits["max_projects"] == 10
        assert limits["max_team_members"] == 5
    
    def test_get_tier_limits_enterprise(self):
        """Test getting limits for ENTERPRISE tier."""
        limits = self.service._get_tier_limits("ENTERPRISE")
        assert limits["max_concurrent_jobs"] == 10
        assert limits["max_images_per_job"] == 10000
        assert limits["max_jobs_per_day"] == 1000
        assert limits["max_projects"] == 100
        assert limits["max_team_members"] == 50
    
    def test_get_tier_limits_defaults_to_free(self):
        """Test getting limits for unknown tier defaults to FREE."""
        limits = self.service._get_tier_limits("UNKNOWN")
        assert limits["max_concurrent_jobs"] == 1  # FREE tier default
        
    @pytest.mark.asyncio
    async def test_validate_request_crawl_job_within_limits(self):
        """Test crawl job validation within limits."""
        # Setup test data in the database
        await self.service.supabase.table("profiles").insert({
            "id": self.user_id,
            "user_tier": "PRO"
        }).execute()
        
        # Test validation
        result = await self.service.validate_request(
            self.user_id, 
            "crawl_job",
            image_count=100
        )
        assert result is True
        
        # Cleanup
        await self.service.supabase.table("profiles").delete().eq("id", self.user_id).execute()
    
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_concurrent_jobs(self):
        """Test crawl job validation when exceeding concurrent jobs limit."""
        # Setup test data in the database
        await self.service.supabase.table("profiles").insert({
            "id": self.user_id,
            "user_tier": "FREE"  # Only 1 concurrent job allowed
        }).execute()
        
        # Create a job to reach the limit
        job_data = {
            "id": "test_job_1",
            "user_id": self.user_id,
            "status": "in_progress",
            "created_at": self.now.isoformat()
        }
        await self.service.supabase.table("crawl_jobs").insert(job_data).execute()
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "crawl_job"
            )
        
        # Cleanup
        await self.service.supabase.table("crawl_jobs").delete().eq("id", "test_job_1").execute()
        await self.service.supabase.table("profiles").delete().eq("id", self.user_id).execute()
    
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_daily_jobs(self):
        """Test crawl job validation when exceeding daily jobs limit."""
        # Setup test data in the database
        await self.service.supabase.table("profiles").insert({
            "id": self.user_id,
            "user_tier": "FREE"  # Only 3 jobs per day
        }).execute()
        
        # Create 3 jobs today to reach the limit
        for i in range(3):
            job_data = {
                "id": f"test_job_{i}",
                "user_id": self.user_id,
                "status": "completed",
                "created_at": self.now.isoformat()
            }
            await self.service.supabase.table("crawl_jobs").insert(job_data).execute()
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "crawl_job"
            )
        
        # Cleanup
        for i in range(3):
            await self.service.supabase.table("crawl_jobs").delete().eq("id", f"test_job_{i}").execute()
        await self.service.supabase.table("profiles").delete().eq("id", self.user_id).execute()
    
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_project_limit(self):
        """Test project creation validation when exceeding project limit."""
        # Setup test data in the database
        await self.service.supabase.table("profiles").insert({
            "id": self.user_id,
            "user_tier": "FREE"  # Only 3 projects allowed
        }).execute()
        
        # Create 3 projects to reach the limit
        for i in range(3):
            project_data = {
                "id": f"project_{i}",
                "owner_id": self.user_id,
                "name": f"Test Project {i}",
                "created_at": self.now.isoformat()
            }
            await self.service.supabase.table("projects").insert(project_data).execute()
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "create_project"
            )
        
        # Cleanup
        for i in range(3):
            await self.service.supabase.table("projects").delete().eq("id", f"project_{i}").execute()
        await self.service.supabase.table("profiles").delete().eq("id", self.user_id).execute()
    
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_team_members(self):
        """Test team member addition validation when exceeding team member limit."""
        # Setup test data in the database
        await self.service.supabase.table("profiles").insert({
            "id": self.user_id,
            "user_tier": "FREE"  # Only 1 team member allowed (the user themselves)
        }).execute()
        
        # Create a team
        team_data = {
            "id": "test_team_1",
            "owner_id": self.user_id,
            "name": "Test Team"
        }
        await self.service.supabase.table("teams").insert(team_data).execute()
        
        # Add one team member to reach the limit
        member_data = {
            "id": "member_1",
            "team_id": "test_team_1",
            "user_id": "another_user_1",
            "role": "member"
        }
        await self.service.supabase.table("team_members").insert(member_data).execute()
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "add_team_member"
            )
        
        # Cleanup
        await self.service.supabase.table("team_members").delete().eq("id", "member_1").execute()
        await self.service.supabase.table("teams").delete().eq("id", "test_team_1").execute()
        await self.service.supabase.table("profiles").delete().eq("id", self.user_id).execute()
    
    @pytest.mark.asyncio
    async def test_get_user_tier_info(self):
        """Test getting user tier information with limits and usage."""
        # Setup test data in the database
        await self.service.supabase.table("profiles").insert({
            "id": self.user_id,
            "user_tier": "PRO"
        }).execute()
        
        # Add some usage data
        job_data = {
            "id": "test_job_1",
            "user_id": self.user_id,
            "status": "completed",
            "created_at": self.now.isoformat()
        }
        await self.service.supabase.table("crawl_jobs").insert(job_data).execute()
        
        # Get tier info
        tier, limits, usage = await self.service.get_user_tier_info(self.user_id)
        
        # Verify results
        assert tier == "PRO"
        assert limits["max_jobs_per_day"] == 20
        assert usage["jobs_today"] == 1
        
        # Cleanup
        await self.service.supabase.table("crawl_jobs").delete().eq("id", "test_job_1").execute()
        await self.service.supabase.table("profiles").delete().eq("id", self.user_id).execute()
