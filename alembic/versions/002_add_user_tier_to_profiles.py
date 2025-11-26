"""Add user_tier column to profiles table

Revision ID: 002
Revises: 001
Create Date: 2025-01-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_tier column to profiles table
    op.add_column(
        "profiles",
        sa.Column(
            "user_tier",
            sa.String(20),
            nullable=False,
            server_default="FREE",
        ),
    )

    # Create index on user_tier
    op.create_index("ix_profiles_user_tier", "profiles", ["user_tier"])

    # Create check constraint for valid tiers
    op.create_check_constraint(
        "ck_profiles_user_tier_valid",
        "profiles",
        "user_tier IN ('FREE', 'PRO', 'ENTERPRISE')",
    )


def downgrade() -> None:
    # Drop check constraint
    op.drop_constraint("ck_profiles_user_tier_valid", "profiles", type_="check")

    # Drop index
    op.drop_index("ix_profiles_user_tier", table_name="profiles")

    # Drop column
    op.drop_column("profiles", "user_tier")
