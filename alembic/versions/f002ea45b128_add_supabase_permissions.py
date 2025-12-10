"""add_supabase_permissions

Revision ID: f002ea45b128
Revises: 898d6843976e
Create Date: 2025-12-10 18:06:19.468205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f002ea45b128'
down_revision: Union[str, None] = '898d6843976e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Grant usage on schema
    op.execute("GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role")

    # Grant all privileges to postgres and service_role (admin access)
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role")
    op.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role")
    op.execute("GRANT ALL ON ALL ROUTINES IN SCHEMA public TO postgres, service_role")

    # Grant access to anon and authenticated (controlled by RLS)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon, authenticated")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated")

    # Ensure future tables get these grants automatically
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres, service_role")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon, authenticated")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres, service_role")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO anon, authenticated")


def downgrade() -> None:
    # Revoke permissions (optional, but good for completeness)
    # Note: Revoking from postgres might be dangerous if it's the owner, 
    # but usually we just want to revert the specific grants to other roles.
    
    # Revert default privileges
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM postgres, service_role")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM anon, authenticated")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM postgres, service_role")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE USAGE, SELECT ON SEQUENCES FROM anon, authenticated")
    
    # Revoke specific grants
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated")
    # We typically don't revoke from postgres/service_role as they are admin roles

