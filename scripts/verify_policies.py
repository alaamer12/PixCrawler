"""
Verification script for dataset policies.
"""
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.policy import ArchivalPolicy, CleanupPolicy
from backend.schemas.policy import ArchivalPolicyCreate, StorageTier
from backend.services.policy import PolicyService

async def verify():
    print("Verifying imports...")
    print(f"ArchivalPolicy model: {ArchivalPolicy}")
    print(f"CleanupPolicy model: {CleanupPolicy}")
    
    print("\nVerifying schema...")
    policy_create = ArchivalPolicyCreate(
        name="Test Policy",
        days_until_archive=30,
        target_tier=StorageTier.COLD
    )
    print(f"Created schema: {policy_create}")
    
    print("\nVerification successful!")

if __name__ == "__main__":
    asyncio.run(verify())
