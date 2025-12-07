"""
Tests for Supabase authentication service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from backend.services.supabase_auth import SupabaseAuthService
from backend.services.crawl_job import RateLimitExceeded

class TestSupabaseAuthServiceTierLimits:
    """Test tier limits and validation in SupabaseAuthService."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Mock get_settings to avoid actual settings loading issues if any
        with patch("backend.services.supabase_auth.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.supabase.url = "https://test.supabase.co"
            mock_settings.supabase.service_role_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            # Mock create_client
            with patch("backend.services.supabase_auth.create_client") as mock_create_client:
                self.mock_supabase = MagicMock()
                mock_create_client.return_value = self.mock_supabase
                self.service = SupabaseAuthService()
        
        self.user_id = "test_user_123"
        self.now = datetime.utcnow()
        
    def _mock_db_response(self, data=None, count=None):
        """Helper to create a mock response object."""
        response = MagicMock()
        response.data = data if data is not None else []
        response.count = count if count is not None else len(response.data)
        return response

    def _setup_chain_mock(self, return_data=None, count=None):
        """Setup a mock for a method chain ending in execute()."""
        mock_execute = MagicMock()
        mock_execute.execute.return_value = self._mock_db_response(return_data, count)
        
        # Create a mock that returns itself for any method call, but has a specific execute
        mock_chain = MagicMock()
        mock_chain.select.return_value = mock_chain
        mock_chain.insert.return_value = mock_chain
        mock_chain.update.return_value = mock_chain
        mock_chain.delete.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.neq.return_value = mock_chain
        mock_chain.gt.return_value = mock_chain
        mock_chain.gte.return_value = mock_chain
        mock_chain.lt.return_value = mock_chain
        mock_chain.lte.return_value = mock_chain
        mock_chain.in_.return_value = mock_chain
        mock_chain.execute = mock_execute.execute
        
        return mock_chain

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
        # Mock detect_user_tier to return PRO
        self.service.detect_user_tier = AsyncMock(return_value="PRO")
        
        # Mock get_user_usage_metrics to return low usage
        self.service.get_user_usage_metrics = AsyncMock(return_value={
            "concurrent_jobs": 0,
            "jobs_today": 0,
            "total_projects": 0,
            "team_members": 0
        })
        
        # Test validation
        result = await self.service.validate_request(
            self.user_id, 
            "crawl_job",
            image_count=100
        )
        assert result is True
        
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_concurrent_jobs(self):
        """Test crawl job validation when exceeding concurrent jobs limit."""
        # Mock detect_user_tier to return FREE
        self.service.detect_user_tier = AsyncMock(return_value="FREE")
        
        # Mock get_user_usage_metrics to return max usage
        self.service.get_user_usage_metrics = AsyncMock(return_value={
            "concurrent_jobs": 1, # Max for FREE is 1
            "jobs_today": 0,
            "total_projects": 0,
            "team_members": 0
        })
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "crawl_job"
            )
    
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_daily_jobs(self):
        """Test crawl job validation when exceeding daily jobs limit."""
        # Mock detect_user_tier to return FREE
        self.service.detect_user_tier = AsyncMock(return_value="FREE")
        
        # Mock get_user_usage_metrics to return max usage
        self.service.get_user_usage_metrics = AsyncMock(return_value={
            "concurrent_jobs": 0,
            "jobs_today": 3, # Max for FREE is 3
            "total_projects": 0,
            "team_members": 0
        })
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "crawl_job"
            )
    
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_project_limit(self):
        """Test project creation validation when exceeding project limit."""
        # Mock detect_user_tier to return FREE
        self.service.detect_user_tier = AsyncMock(return_value="FREE")
        
        # Mock get_user_usage_metrics
        self.service.get_user_usage_metrics = AsyncMock(return_value={
            "concurrent_jobs": 0,
            "jobs_today": 0,
            "total_projects": 3, # Max for FREE is 3
            "team_members": 0
        })
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "create_project"
            )
    
    @pytest.mark.asyncio
    async def test_validate_request_exceeds_team_members(self):
        """Test team member addition validation when exceeding team member limit."""
        # Mock detect_user_tier to return FREE
        self.service.detect_user_tier = AsyncMock(return_value="FREE")
        
        # Mock get_user_usage_metrics
        self.service.get_user_usage_metrics = AsyncMock(return_value={
            "concurrent_jobs": 0,
            "jobs_today": 0,
            "total_projects": 0,
            "team_members": 1 # Max for FREE is 1
        })
        
        # Test validation should raise RateLimitExceeded
        with pytest.raises(RateLimitExceeded):
            await self.service.validate_request(
                self.user_id,
                "add_team_member"
            )
    
    @pytest.mark.asyncio
    async def test_get_user_tier_info(self):
        """Test getting user tier information with limits and usage."""
        # Mock get_user_tier
        self.service.get_user_tier = AsyncMock(return_value="PRO")
        
        # Mock get_user_usage_metrics
        self.service.get_user_usage_metrics = AsyncMock(return_value={
            "concurrent_jobs": 0,
            "jobs_today": 1,
            "total_projects": 0,
            "team_members": 0
        })
        
        # Get tier info
        tier, limits, usage = await self.service.get_user_tier_info(self.user_id)
        
        # Verify results
        assert tier == "PRO"
        assert limits["max_jobs_per_day"] == 20
        assert usage["jobs_today"] == 1
