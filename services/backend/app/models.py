from typing import Dict, Optional

from pydantic import BaseModel


class ConnectorSpec(BaseModel):
    connector_type: str
    connection_string: str
    schema_name: str = ""
    direction: str = "source"
    options: Dict[str, str] = {}


class TableProfile(BaseModel):
    table_name: str
    column_count: int
    field_count: int


class MappingWorkbenchUpdate(BaseModel):
    workbench_id: str
    mapping_class: Optional[str] = None
    primary_source_table: Optional[str] = None
    primary_source_field: Optional[str] = None
    transformation_rule: Optional[str] = None
    notes: Optional[str] = None
    updated_by: str = "ui_user"


class MappingWorkbenchTransition(BaseModel):
    workbench_id: str
    status: str
    updated_by: str = "ui_user"
    notes: Optional[str] = None


class AuthLoginRequest(BaseModel):
    username_or_email: str
    password: str
    org_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None


class AuthRegisterRequest(BaseModel):
    username: str
    email: str
    display_name: str
    password: str
    requested_org_id: str


class RegistrationReviewRequest(BaseModel):
    role: str = "org_dm_engineer"
    reason: Optional[str] = None


class CreateNameRequest(BaseModel):
    name: str


class ContextSwitchRequest(BaseModel):
    org_id: str
    workspace_id: str
    project_id: str


class UserStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class MembershipRoleUpdateRequest(BaseModel):
    role: str
    reason: Optional[str] = None


class MembershipCreateRequest(BaseModel):
    org_id: str
    role: str
    reason: Optional[str] = None


class RoleCreateRequest(BaseModel):
    role: str
    permissions: list[str] = []


class RolePermissionsUpdateRequest(BaseModel):
    permissions: list[str] = []


class UserActionRequest(BaseModel):
    reason: Optional[str] = None
