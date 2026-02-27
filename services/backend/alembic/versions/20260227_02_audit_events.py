"""add immutable audit events table

Revision ID: 20260227_02
Revises: 20260227_01
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260227_02"
down_revision: Union[str, None] = "20260227_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            created_at_utc VARCHAR(64) NOT NULL,
            event_type VARCHAR(128) NOT NULL,
            outcome VARCHAR(32) NOT NULL,
            actor_user_id VARCHAR(64) NOT NULL DEFAULT '',
            actor_role VARCHAR(64) NOT NULL DEFAULT '',
            actor_org_id VARCHAR(64) NOT NULL DEFAULT '',
            actor_workspace_id VARCHAR(64) NOT NULL DEFAULT '',
            actor_project_id VARCHAR(64) NOT NULL DEFAULT '',
            target_type VARCHAR(64) NOT NULL DEFAULT '',
            target_id VARCHAR(128) NOT NULL DEFAULT '',
            request_id VARCHAR(128) NOT NULL DEFAULT '',
            request_ip VARCHAR(128) NOT NULL DEFAULT '',
            user_agent TEXT NOT NULL DEFAULT '',
            details_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_created_at_utc ON audit_events (created_at_utc)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_event_type ON audit_events (event_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_outcome ON audit_events (outcome)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_actor_user_id ON audit_events (actor_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_actor_role ON audit_events (actor_role)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_actor_org_id ON audit_events (actor_org_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_target_type ON audit_events (target_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_target_id ON audit_events (target_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_request_id ON audit_events (request_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_events")
