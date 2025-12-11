"""add_supbase_auth_hooks

Revision ID: 898d6843976e
Revises: 20240127_001
Create Date: 2025-12-10 17:55:28.322575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '898d6843976e'
down_revision: Union[str, None] = '20240127_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. Enable RLS on profiles ---
    op.execute("ALTER TABLE profiles ENABLE ROW LEVEL SECURITY")

    # --- 2. Create RLS Policies ---
    # Note: We use specific names to avoid conflicts if they already exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'profiles' AND policyname = 'Users can view own profile'
            ) THEN
                CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'profiles' AND policyname = 'Users can update own profile'
            ) THEN
                CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'profiles' AND policyname = 'Users can insert own profile'
            ) THEN
                CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
            END IF;
        END $$;
    """)

    # --- 3. Create Function: handle_new_user ---
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO public.profiles (id, email, full_name, avatar_url)
            VALUES (
                NEW.id,
                NEW.email,
                COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
                COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture')
            )
            ON CONFLICT (id) DO NOTHING;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # --- 4. Create Trigger: on_auth_user_created ---
    # We drop it first to ensure we can recreate it cleanly
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users")
    op.execute("""
        CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
    """)

    # --- 5. Create Function: handle_updated_at ---
    op.execute("""
        CREATE OR REPLACE FUNCTION public.handle_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # --- 6. Create Trigger: handle_updated_at ---
    op.execute("DROP TRIGGER IF EXISTS handle_updated_at ON profiles")
    op.execute("""
        CREATE TRIGGER handle_updated_at
        BEFORE UPDATE ON profiles
        FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
    """)


def downgrade() -> None:
    # Remove triggers and functions in reverse order
    op.execute("DROP TRIGGER IF EXISTS handle_updated_at ON profiles")
    op.execute("DROP FUNCTION IF EXISTS public.handle_updated_at()")
    
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_user()")
    
    op.execute("DROP POLICY IF EXISTS \"Users can insert own profile\" ON profiles")
    op.execute("DROP POLICY IF EXISTS \"Users can update own profile\" ON profiles")
    op.execute("DROP POLICY IF EXISTS \"Users can view own profile\" ON profiles")
    
    op.execute("ALTER TABLE profiles DISABLE ROW LEVEL SECURITY")

