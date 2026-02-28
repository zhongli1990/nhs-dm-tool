"""add user lifecycle security columns

Revision ID: 20260228_03
Revises: 20260227_02
Create Date: 2026-02-28
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260228_03"
down_revision: Union[str, None] = "20260227_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at_utc VARCHAR(64) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_count INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until_utc VARCHAR(64) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS session_revoked_at_utc VARCHAR(64) NOT NULL DEFAULT ''")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_failed_login_count ON users (failed_login_count)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_locked_until_utc ON users (locked_until_utc)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_locked_until_utc")
    op.execute("DROP INDEX IF EXISTS ix_users_failed_login_count")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS session_revoked_at_utc")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS locked_until_utc")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS failed_login_count")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS last_login_at_utc")
