"""baseline enterprise schema for auth/rbac/runtime state

Revision ID: 20260227_01
Revises:
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260227_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(64) PRIMARY KEY,
            username VARCHAR(128) UNIQUE,
            email VARCHAR(320) UNIQUE,
            display_name VARCHAR(256) NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
            is_super_admin BOOLEAN NOT NULL DEFAULT FALSE,
            created_at_utc VARCHAR(64) NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_status ON users (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_is_super_admin ON users (is_super_admin)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(256) NOT NULL,
            slug VARCHAR(256) UNIQUE,
            status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
            created_at_utc VARCHAR(64) NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organizations_status ON organizations (status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS workspaces (
            id VARCHAR(64) PRIMARY KEY,
            org_id VARCHAR(64) NOT NULL REFERENCES organizations(id),
            name VARCHAR(256) NOT NULL,
            slug VARCHAR(256) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
            created_at_utc VARCHAR(64) NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspaces_org_id ON workspaces (org_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspaces_slug ON workspaces (slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspaces_status ON workspaces (status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id VARCHAR(64) PRIMARY KEY,
            workspace_id VARCHAR(64) NOT NULL REFERENCES workspaces(id),
            name VARCHAR(256) NOT NULL,
            slug VARCHAR(256) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
            created_at_utc VARCHAR(64) NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_workspace_id ON projects (workspace_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_slug ON projects (slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_status ON projects (status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_memberships (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL REFERENCES users(id),
            org_id VARCHAR(64) NOT NULL REFERENCES organizations(id),
            role VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
            created_at_utc VARCHAR(64) NOT NULL,
            CONSTRAINT uq_membership_user_org UNIQUE (user_id, org_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_organization_memberships_user_id ON organization_memberships (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organization_memberships_org_id ON organization_memberships (org_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organization_memberships_role ON organization_memberships (role)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organization_memberships_status ON organization_memberships (status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS registration_requests (
            id VARCHAR(64) PRIMARY KEY,
            username VARCHAR(128) NOT NULL,
            email VARCHAR(320) NOT NULL,
            display_name VARCHAR(256) NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL,
            requested_org_id VARCHAR(64) NOT NULL REFERENCES organizations(id),
            status VARCHAR(64) NOT NULL DEFAULT 'PENDING_APPROVAL',
            reviewed_by VARCHAR(64) NOT NULL DEFAULT '',
            reviewed_at_utc VARCHAR(64) NOT NULL DEFAULT '',
            review_reason TEXT NOT NULL DEFAULT '',
            created_at_utc VARCHAR(64) NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_registration_requests_username ON registration_requests (username)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_registration_requests_email ON registration_requests (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_registration_requests_requested_org_id ON registration_requests (requested_org_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_registration_requests_status ON registration_requests (status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            id SERIAL PRIMARY KEY,
            role VARCHAR(64) NOT NULL,
            permission VARCHAR(128) NOT NULL,
            CONSTRAINT uq_role_permission UNIQUE (role, permission)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_role_permissions_role ON role_permissions (role)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_role_permissions_permission ON role_permissions (permission)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS mapping_workbench (
            id SERIAL PRIMARY KEY,
            workbench_id VARCHAR(512) UNIQUE,
            target_table VARCHAR(256) NOT NULL,
            target_field VARCHAR(256) NOT NULL,
            mapping_class VARCHAR(128) NOT NULL DEFAULT '',
            primary_source_table VARCHAR(256) NOT NULL DEFAULT '',
            primary_source_field VARCHAR(256) NOT NULL DEFAULT '',
            transformation_rule TEXT NOT NULL DEFAULT '',
            status VARCHAR(64) NOT NULL DEFAULT 'DRAFT',
            notes TEXT NOT NULL DEFAULT '',
            last_updated_by VARCHAR(128) NOT NULL DEFAULT 'system',
            last_updated_at_utc VARCHAR(64) NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_mapping_workbench_workbench_id ON mapping_workbench (workbench_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mapping_workbench_target_table ON mapping_workbench (target_table)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mapping_workbench_target_field ON mapping_workbench (target_field)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mapping_workbench_status ON mapping_workbench (status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS quality_history (
            id SERIAL PRIMARY KEY,
            ts_utc VARCHAR(64) NOT NULL,
            event VARCHAR(128) NOT NULL DEFAULT '',
            error_count INTEGER NOT NULL DEFAULT 0,
            warning_count INTEGER NOT NULL DEFAULT 0,
            crosswalk_rejects INTEGER NOT NULL DEFAULT 0,
            population_ratio DOUBLE PRECISION NOT NULL DEFAULT 0,
            tables_written INTEGER NOT NULL DEFAULT 0,
            unresolved_mapping INTEGER NOT NULL DEFAULT 0,
            release_status VARCHAR(64) NOT NULL DEFAULT 'UNKNOWN'
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_quality_history_ts_utc ON quality_history (ts_utc)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS quality_kpi_config (
            id SERIAL PRIMARY KEY,
            kpi_id VARCHAR(128) NOT NULL,
            label VARCHAR(256) NOT NULL,
            threshold DOUBLE PRECISION NOT NULL DEFAULT 0,
            direction VARCHAR(16) NOT NULL DEFAULT 'max',
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            format VARCHAR(16) NOT NULL DEFAULT 'int',
            CONSTRAINT uq_quality_kpi_id UNIQUE (kpi_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_quality_kpi_config_kpi_id ON quality_kpi_config (kpi_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS quality_kpi_config")
    op.execute("DROP TABLE IF EXISTS quality_history")
    op.execute("DROP TABLE IF EXISTS mapping_workbench")
    op.execute("DROP TABLE IF EXISTS role_permissions")
    op.execute("DROP TABLE IF EXISTS registration_requests")
    op.execute("DROP TABLE IF EXISTS organization_memberships")
    op.execute("DROP TABLE IF EXISTS projects")
    op.execute("DROP TABLE IF EXISTS workspaces")
    op.execute("DROP TABLE IF EXISTS organizations")
    op.execute("DROP TABLE IF EXISTS users")
