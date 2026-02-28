import json
import os
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from .security import hash_password, verify_password


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


def _to_epoch(ts_utc: str) -> int:
    try:
        return int(datetime.fromisoformat(ts_utc).timestamp())
    except Exception:
        return 0


DEFAULT_DMM_PERMISSIONS: Dict[str, Set[str]] = {
    "super_admin": {"*"},
    "org_admin": {"org.manage", "workspace.manage", "project.manage", "project.execute", "project.design", "project.quality", "registration.review"},
    "org_dm_engineer": {"project.execute", "project.design", "project.quality"},
    "org_data_architect": {"project.execute", "project.design", "project.quality"},
    "org_dq_lead": {"project.execute", "project.design", "project.quality"},
    "org_clinical_reviewer": {"project.execute", "project.design", "project.quality"},
    "org_release_manager": {"project.execute", "project.design", "project.quality"},
}
SYSTEM_DMM_ROLES: Set[str] = set(DEFAULT_DMM_PERMISSIONS.keys())


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(256), default="")
    password_hash: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    last_login_at_utc: Mapped[str] = mapped_column(String(64), default="")
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until_utc: Mapped[str] = mapped_column(String(64), default="")
    session_revoked_at_utc: Mapped[str] = mapped_column(String(64), default="")
    created_at_utc: Mapped[str] = mapped_column(String(64), default=_now)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    slug: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    created_at_utc: Mapped[str] = mapped_column(String(64), default=_now)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(256))
    slug: Mapped[str] = mapped_column(String(256), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    created_at_utc: Mapped[str] = mapped_column(String(64), default=_now)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(256))
    slug: Mapped[str] = mapped_column(String(256), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    created_at_utc: Mapped[str] = mapped_column(String(64), default=_now)


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (UniqueConstraint("user_id", "org_id", name="uq_membership_user_org"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), index=True)
    role: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    created_at_utc: Mapped[str] = mapped_column(String(64), default=_now)


class RegistrationRequest(Base):
    __tablename__ = "registration_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(128), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    display_name: Mapped[str] = mapped_column(String(256), default="")
    password_hash: Mapped[str] = mapped_column(Text)
    requested_org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), index=True)
    status: Mapped[str] = mapped_column(String(64), default="PENDING_APPROVAL", index=True)
    reviewed_by: Mapped[str] = mapped_column(String(64), default="")
    reviewed_at_utc: Mapped[str] = mapped_column(String(64), default="")
    review_reason: Mapped[str] = mapped_column(Text, default="")
    created_at_utc: Mapped[str] = mapped_column(String(64), default=_now)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role", "permission", name="uq_role_permission"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(64), index=True)
    permission: Mapped[str] = mapped_column(String(128), index=True)


class _FileSaaSStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self._seed_data())

    def _seed_data(self) -> Dict[str, object]:
        org_id = str(uuid.uuid4())
        ws_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        super_id = str(uuid.uuid4())
        org_admin_id = str(uuid.uuid4())
        password = os.environ.get("DMM_BOOTSTRAP_ADMIN_PASSWORD", "ChangeMeNow!123")
        return {
            "users": [
                {
                    "id": super_id,
                    "username": os.environ.get("DMM_BOOTSTRAP_ADMIN_USERNAME", "superadmin"),
                    "email": os.environ.get("DMM_BOOTSTRAP_ADMIN_EMAIL", "superadmin@openli.local"),
                    "display_name": "OpenLI Super Admin",
                    "password_hash": hash_password(password),
                    "status": "ACTIVE",
                    "is_super_admin": True,
                    "last_login_at_utc": "",
                    "failed_login_count": 0,
                    "locked_until_utc": "",
                    "session_revoked_at_utc": "",
                    "created_at_utc": _now(),
                },
                {
                    "id": org_admin_id,
                    "username": "qvh_admin",
                    "email": "qvh.admin@openli.local",
                    "display_name": "QVH Org Admin",
                    "password_hash": hash_password(password),
                    "status": "ACTIVE",
                    "is_super_admin": False,
                    "last_login_at_utc": "",
                    "failed_login_count": 0,
                    "locked_until_utc": "",
                    "session_revoked_at_utc": "",
                    "created_at_utc": _now(),
                },
            ],
            "organizations": [{"id": org_id, "name": "QVH", "slug": "qvh", "status": "ACTIVE", "created_at_utc": _now()}],
            "workspaces": [{"id": ws_id, "org_id": org_id, "name": "PAS EPR", "slug": "pas-epr", "status": "ACTIVE", "created_at_utc": _now()}],
            "projects": [{"id": project_id, "workspace_id": ws_id, "name": "PAS18.4 Migration", "slug": "pas18-4-migration", "status": "ACTIVE", "created_at_utc": _now()}],
            "organization_memberships": [
                {"user_id": super_id, "org_id": org_id, "role": "super_admin", "status": "ACTIVE", "created_at_utc": _now()},
                {"user_id": org_admin_id, "org_id": org_id, "role": "org_admin", "status": "ACTIVE", "created_at_utc": _now()},
            ],
            "registration_requests": [],
        }

    def _read(self) -> Dict[str, object]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: Dict[str, object]) -> None:
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def authenticate(self, username_or_email: str, password: str) -> Optional[Dict[str, object]]:
        max_attempts = int(os.environ.get("DMM_AUTH_LOCK_MAX_ATTEMPTS", "5"))
        lock_minutes = int(os.environ.get("DMM_AUTH_LOCK_MINUTES", "15"))
        with self.lock:
            data = self._read()
            for user in data["users"]:
                if username_or_email.lower() in {str(user.get("username", "")).lower(), str(user.get("email", "")).lower()}:
                    now = datetime.now(timezone.utc)
                    lock_until = str(user.get("locked_until_utc", "")).strip()
                    if lock_until and _to_epoch(lock_until) > int(now.timestamp()):
                        user["status"] = "LOCKED"
                        self._write(data)
                        return None
                    if str(user.get("status", "ACTIVE")).upper() != "ACTIVE":
                        return None
                    if verify_password(password, str(user.get("password_hash", ""))):
                        user["failed_login_count"] = 0
                        user["locked_until_utc"] = ""
                        user["last_login_at_utc"] = now.isoformat()
                        self._write(data)
                        return user
                    failed = int(user.get("failed_login_count", 0) or 0) + 1
                    user["failed_login_count"] = failed
                    if failed >= max_attempts:
                        user["status"] = "LOCKED"
                        user["locked_until_utc"] = (now + timedelta(minutes=lock_minutes)).isoformat()
                    self._write(data)
                    return None
            return None

    def list_user_memberships(self, user_id: str) -> List[Dict[str, object]]:
        with self.lock:
            data = self._read()
            memberships = [m for m in data["organization_memberships"] if m.get("user_id") == user_id and m.get("status") == "ACTIVE"]
            orgs = {o["id"]: o for o in data["organizations"]}
            result = []
            for m in memberships:
                org = orgs.get(m.get("org_id"))
                if org:
                    result.append({"org_id": org["id"], "org_name": org["name"], "role": m.get("role", "org_user")})
            return result

    def list_orgs_for_user(self, user: Dict[str, object]) -> List[Dict[str, object]]:
        with self.lock:
            data = self._read()
            if user.get("is_super_admin"):
                return data["organizations"]
            allowed = {m["org_id"] for m in data["organization_memberships"] if m.get("user_id") == user.get("id") and m.get("status") == "ACTIVE"}
            return [o for o in data["organizations"] if o["id"] in allowed]

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, object]]:
        with self.lock:
            data = self._read()
            for u in data["users"]:
                if u.get("id") == user_id:
                    return u
            return None

    def user_has_org(self, user_id: str, org_id: str) -> bool:
        with self.lock:
            data = self._read()
            users = {u["id"]: u for u in data["users"]}
            user = users.get(user_id)
            if not user:
                return False
            if user.get("is_super_admin"):
                return True
            for m in data["organization_memberships"]:
                if m.get("user_id") == user_id and m.get("org_id") == org_id and m.get("status") == "ACTIVE":
                    return True
            return False

    def workspace_belongs_to_org(self, workspace_id: str, org_id: str) -> bool:
        with self.lock:
            data = self._read()
            return any(w.get("id") == workspace_id and w.get("org_id") == org_id for w in data["workspaces"])

    def project_belongs_to_workspace(self, project_id: str, workspace_id: str) -> bool:
        with self.lock:
            data = self._read()
            return any(p.get("id") == project_id and p.get("workspace_id") == workspace_id for p in data["projects"])

    def list_workspaces_for_org(self, org_id: str) -> List[Dict[str, object]]:
        with self.lock:
            data = self._read()
            return [w for w in data["workspaces"] if w.get("org_id") == org_id]

    def list_projects_for_workspace(self, workspace_id: str) -> List[Dict[str, object]]:
        with self.lock:
            data = self._read()
            return [p for p in data["projects"] if p.get("workspace_id") == workspace_id]

    def create_registration_request(self, username: str, email: str, display_name: str, password: str, requested_org_id: str) -> Dict[str, object]:
        with self.lock:
            data = self._read()
            for u in data["users"]:
                if username.lower() == str(u.get("username", "")).lower() or email.lower() == str(u.get("email", "")).lower():
                    raise ValueError("username or email already exists")
            for req in data["registration_requests"]:
                if req.get("status") == "PENDING_APPROVAL" and (
                    req.get("username", "").lower() == username.lower() or req.get("email", "").lower() == email.lower()
                ):
                    raise ValueError("pending registration already exists")
            org_ids = {o["id"] for o in data["organizations"]}
            if requested_org_id not in org_ids:
                raise ValueError("requested organization not found")
            req = {
                "id": str(uuid.uuid4()),
                "username": username,
                "email": email,
                "display_name": display_name,
                "password_hash": hash_password(password),
                "requested_org_id": requested_org_id,
                "status": "PENDING_APPROVAL",
                "reviewed_by": "",
                "reviewed_at_utc": "",
                "created_at_utc": _now(),
            }
            data["registration_requests"].append(req)
            self._write(data)
            return req

    def list_registration_requests(self, status: Optional[str] = None) -> List[Dict[str, object]]:
        with self.lock:
            data = self._read()
            rows = list(data["registration_requests"])
            if status:
                rows = [r for r in rows if str(r.get("status", "")).upper() == status.upper()]
            return rows

    def approve_registration(self, request_id: str, reviewer_user_id: str, role: str = "org_dm_engineer") -> Dict[str, object]:
        with self.lock:
            data = self._read()
            req = next((row for row in data["registration_requests"] if row.get("id") == request_id), None)
            if not req:
                raise ValueError("request not found")
            if req.get("status") != "PENDING_APPROVAL":
                raise ValueError("request is not pending approval")
            user = {
                "id": str(uuid.uuid4()),
                "username": req["username"],
                "email": req["email"],
                "display_name": req["display_name"],
                "password_hash": req["password_hash"],
                "status": "ACTIVE",
                "is_super_admin": False,
                "created_at_utc": _now(),
            }
            data["users"].append(user)
            data["organization_memberships"].append(
                {"user_id": user["id"], "org_id": req["requested_org_id"], "role": role, "status": "ACTIVE", "created_at_utc": _now()}
            )
            req["status"] = "APPROVED"
            req["reviewed_by"] = reviewer_user_id
            req["reviewed_at_utc"] = _now()
            self._write(data)
            return {"request": req, "user": user}

    def reject_registration(self, request_id: str, reviewer_user_id: str, reason: str = "") -> Dict[str, object]:
        with self.lock:
            data = self._read()
            for req in data["registration_requests"]:
                if req.get("id") == request_id:
                    if req.get("status") != "PENDING_APPROVAL":
                        raise ValueError("request is not pending approval")
                    req["status"] = "REJECTED"
                    req["reviewed_by"] = reviewer_user_id
                    req["reviewed_at_utc"] = _now()
                    req["review_reason"] = reason
                    self._write(data)
                    return req
            raise ValueError("request not found")

    def create_org(self, name: str) -> Dict[str, object]:
        with self.lock:
            data = self._read()
            slug = _slugify(name)
            if any(o.get("slug") == slug for o in data["organizations"]):
                raise ValueError("organization slug already exists")
            row = {"id": str(uuid.uuid4()), "name": name, "slug": slug, "status": "ACTIVE", "created_at_utc": _now()}
            data["organizations"].append(row)
            self._write(data)
            return row

    def create_workspace(self, org_id: str, name: str) -> Dict[str, object]:
        with self.lock:
            data = self._read()
            if org_id not in {o["id"] for o in data["organizations"]}:
                raise ValueError("organization not found")
            slug = _slugify(name)
            row = {"id": str(uuid.uuid4()), "org_id": org_id, "name": name, "slug": slug, "status": "ACTIVE", "created_at_utc": _now()}
            data["workspaces"].append(row)
            self._write(data)
            return row

    def create_project(self, workspace_id: str, name: str) -> Dict[str, object]:
        with self.lock:
            data = self._read()
            if workspace_id not in {w["id"] for w in data["workspaces"]}:
                raise ValueError("workspace not found")
            slug = _slugify(name)
            row = {"id": str(uuid.uuid4()), "workspace_id": workspace_id, "name": name, "slug": slug, "status": "ACTIVE", "created_at_utc": _now()}
            data["projects"].append(row)
            self._write(data)
            return row

    def list_org_users(self, org_id: str) -> List[Dict[str, object]]:
        with self.lock:
            data = self._read()
            users = {u["id"]: u for u in data["users"]}
            result = []
            for m in data["organization_memberships"]:
                if m.get("org_id") != org_id or m.get("status") != "ACTIVE":
                    continue
                u = users.get(m.get("user_id"))
                if not u:
                    continue
                result.append(
                    {
                        "user_id": u["id"],
                        "username": u.get("username"),
                        "email": u.get("email"),
                        "display_name": u.get("display_name"),
                        "role": m.get("role", "org_user"),
                        "status": u.get("status", "ACTIVE"),
                    }
                )
            return result

    def list_permissions_for_role(self, role: str) -> List[str]:
        role_norm = role.strip()
        with self.lock:
            data = self._read()
            custom = data.get("custom_role_permissions", {})
            if role_norm in custom:
                return sorted({str(p).strip() for p in custom.get(role_norm, []) if str(p).strip()})
        return sorted(DEFAULT_DMM_PERMISSIONS.get(role_norm, set()))

    def list_roles(self) -> List[str]:
        with self.lock:
            data = self._read()
            custom = data.get("custom_role_permissions", {})
            roles = set(DEFAULT_DMM_PERMISSIONS.keys())
            roles.update(str(k).strip() for k in custom.keys() if str(k).strip())
            return sorted(roles)

    def list_users_with_memberships(self) -> List[Dict[str, object]]:
        with self.lock:
            data = self._read()
            users = list(data.get("users", []))
            orgs = {str(o.get("id")): o for o in data.get("organizations", [])}
            memberships_by_user: Dict[str, List[Dict[str, object]]] = {}
            for m in data.get("organization_memberships", []):
                uid = str(m.get("user_id", ""))
                org_id = str(m.get("org_id", ""))
                row = {
                    "org_id": org_id,
                    "org_name": str(orgs.get(org_id, {}).get("name", "")),
                    "role": str(m.get("role", "")),
                    "status": str(m.get("status", "ACTIVE")),
                    "created_at_utc": str(m.get("created_at_utc", "")),
                }
                memberships_by_user.setdefault(uid, []).append(row)
            rows: List[Dict[str, object]] = []
            for u in users:
                user_id = str(u.get("id", ""))
                rows.append(
                    {
                        "id": user_id,
                        "username": str(u.get("username", "")),
                        "email": str(u.get("email", "")),
                        "display_name": str(u.get("display_name", "")),
                        "status": str(u.get("status", "ACTIVE")),
                        "is_super_admin": bool(u.get("is_super_admin", False)),
                        "last_login_at_utc": str(u.get("last_login_at_utc", "")),
                        "failed_login_count": int(u.get("failed_login_count", 0) or 0),
                        "locked_until_utc": str(u.get("locked_until_utc", "")),
                        "session_revoked_at_utc": str(u.get("session_revoked_at_utc", "")),
                        "created_at_utc": str(u.get("created_at_utc", "")),
                        "memberships": memberships_by_user.get(user_id, []),
                    }
                )
            return rows

    def update_user_status(self, user_id: str, status: str) -> Dict[str, object]:
        status_norm = status.strip().upper()
        with self.lock:
            data = self._read()
            for user in data.get("users", []):
                if str(user.get("id")) != user_id:
                    continue
                user["status"] = status_norm
                self._write(data)
                return {
                    "id": str(user.get("id", "")),
                    "username": str(user.get("username", "")),
                    "email": str(user.get("email", "")),
                    "display_name": str(user.get("display_name", "")),
                    "status": status_norm,
                    "is_super_admin": bool(user.get("is_super_admin", False)),
                    "last_login_at_utc": str(user.get("last_login_at_utc", "")),
                    "failed_login_count": int(user.get("failed_login_count", 0) or 0),
                    "locked_until_utc": str(user.get("locked_until_utc", "")),
                    "session_revoked_at_utc": str(user.get("session_revoked_at_utc", "")),
                    "created_at_utc": str(user.get("created_at_utc", "")),
                }
            raise ValueError("user not found")

    def unlock_user(self, user_id: str) -> Dict[str, object]:
        with self.lock:
            data = self._read()
            for user in data.get("users", []):
                if str(user.get("id", "")) != user_id:
                    continue
                user["status"] = "ACTIVE"
                user["failed_login_count"] = 0
                user["locked_until_utc"] = ""
                self._write(data)
                return user
            raise ValueError("user not found")

    def revoke_user_sessions(self, user_id: str) -> Dict[str, object]:
        with self.lock:
            data = self._read()
            for user in data.get("users", []):
                if str(user.get("id", "")) != user_id:
                    continue
                user["session_revoked_at_utc"] = _now()
                self._write(data)
                return user
            raise ValueError("user not found")

    def is_token_revoked(self, user_id: str, token_iat: int) -> bool:
        with self.lock:
            data = self._read()
            for user in data.get("users", []):
                if str(user.get("id", "")) != user_id:
                    continue
                revoked = str(user.get("session_revoked_at_utc", "")).strip()
                return bool(revoked and _to_epoch(revoked) >= int(token_iat))
            return True

    def upsert_user_membership_role(self, user_id: str, org_id: str, role: str) -> Dict[str, object]:
        role_norm = role.strip()
        with self.lock:
            data = self._read()
            if user_id not in {str(u.get("id", "")) for u in data.get("users", [])}:
                raise ValueError("user not found")
            if org_id not in {str(o.get("id", "")) for o in data.get("organizations", [])}:
                raise ValueError("organization not found")
            roles = set(self.list_roles())
            if role_norm not in roles:
                raise ValueError("unknown role")

            for m in data.get("organization_memberships", []):
                if str(m.get("user_id", "")) == user_id and str(m.get("org_id", "")) == org_id:
                    m["role"] = role_norm
                    m["status"] = "ACTIVE"
                    self._write(data)
                    return {
                        "user_id": user_id,
                        "org_id": org_id,
                        "role": role_norm,
                        "status": "ACTIVE",
                    }

            data.setdefault("organization_memberships", []).append(
                {
                    "user_id": user_id,
                    "org_id": org_id,
                    "role": role_norm,
                    "status": "ACTIVE",
                    "created_at_utc": _now(),
                }
            )
            self._write(data)
            return {
                "user_id": user_id,
                "org_id": org_id,
                "role": role_norm,
                "status": "ACTIVE",
            }

    def remove_user_membership(self, user_id: str, org_id: str) -> Dict[str, object]:
        with self.lock:
            data = self._read()
            for m in data.get("organization_memberships", []):
                if str(m.get("user_id", "")) != user_id or str(m.get("org_id", "")) != org_id:
                    continue
                m["status"] = "DISABLED"
                self._write(data)
                return {
                    "user_id": user_id,
                    "org_id": org_id,
                    "role": str(m.get("role", "")),
                    "status": "DISABLED",
                }
            raise ValueError("membership not found")

    def create_role(self, role: str, permissions: List[str]) -> Dict[str, object]:
        role_norm = role.strip()
        if not role_norm:
            raise ValueError("role is required")
        if role_norm in SYSTEM_DMM_ROLES:
            raise ValueError("cannot create reserved system role")
        perms = sorted({p.strip() for p in permissions if p.strip()})
        if not perms:
            raise ValueError("at least one permission is required")
        with self.lock:
            data = self._read()
            data.setdefault("custom_role_permissions", {})
            custom = data["custom_role_permissions"]
            if role_norm in custom:
                raise ValueError("role already exists")
            custom[role_norm] = perms
            self._write(data)
            return {"role": role_norm, "permissions": perms}

    def set_role_permissions(self, role: str, permissions: List[str]) -> Dict[str, object]:
        role_norm = role.strip()
        if role_norm in SYSTEM_DMM_ROLES:
            raise ValueError("cannot modify reserved system role in file mode")
        perms = sorted({p.strip() for p in permissions if p.strip()})
        if not perms:
            raise ValueError("at least one permission is required")
        with self.lock:
            data = self._read()
            data.setdefault("custom_role_permissions", {})
            custom = data["custom_role_permissions"]
            if role_norm not in custom:
                raise ValueError("role not found")
            custom[role_norm] = perms
            self._write(data)
            return {"role": role_norm, "permissions": perms}

    def delete_role(self, role: str) -> Dict[str, object]:
        role_norm = role.strip()
        if role_norm in SYSTEM_DMM_ROLES:
            raise ValueError("cannot delete reserved system role")
        with self.lock:
            data = self._read()
            for m in data.get("organization_memberships", []):
                if str(m.get("role", "")) == role_norm and str(m.get("status", "ACTIVE")) == "ACTIVE":
                    raise ValueError("role is in use by active memberships")
            data.setdefault("custom_role_permissions", {})
            custom = data["custom_role_permissions"]
            if role_norm not in custom:
                raise ValueError("role not found")
            perms = custom.pop(role_norm)
            self._write(data)
            return {"role": role_norm, "permissions": perms}


class _PostgresSaaSStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        if os.environ.get("DM_SCHEMA_AUTOCREATE", "false").strip().lower() in {"true", "1", "yes"}:
            Base.metadata.create_all(self.engine)
        self._seed_if_empty()

    def _session(self) -> Session:
        return self.SessionLocal()

    def _seed_if_empty(self) -> None:
        with self._session() as session:
            if session.scalar(select(User.id).limit(1)):
                self._seed_role_permissions(session)
                session.commit()
                return

            try:
                # Recover safely from a partial bootstrap attempt.
                session.execute(delete(OrganizationMembership))
                session.execute(delete(Project))
                session.execute(delete(Workspace))
                session.execute(delete(Organization))
                session.execute(delete(RegistrationRequest))
                session.commit()

                org_id = str(uuid.uuid4())
                ws_id = str(uuid.uuid4())
                project_id = str(uuid.uuid4())
                super_id = str(uuid.uuid4())
                org_admin_id = str(uuid.uuid4())
                now = _now()

                admin_username = os.environ.get("DMM_BOOTSTRAP_ADMIN_USERNAME", "superadmin")
                admin_email = os.environ.get("DMM_BOOTSTRAP_ADMIN_EMAIL", "superadmin@openli.local")
                admin_password = os.environ.get("DMM_BOOTSTRAP_ADMIN_PASSWORD", "ChangeMeNow!123")
                if admin_password == "ChangeMeNow!123":
                    print("[DMM][WARN] DMM_BOOTSTRAP_ADMIN_PASSWORD is using default value; set a strong secret for production.")

                session.add(
                    User(
                        id=super_id,
                        username=admin_username,
                        email=admin_email,
                        display_name="OpenLI Super Admin",
                        password_hash=hash_password(admin_password),
                        status="ACTIVE",
                        is_super_admin=True,
                        last_login_at_utc="",
                        failed_login_count=0,
                        locked_until_utc="",
                        session_revoked_at_utc="",
                        created_at_utc=now,
                    )
                )
                session.add(
                    User(
                        id=org_admin_id,
                        username="qvh_admin",
                        email="qvh.admin@openli.local",
                        display_name="QVH Org Admin",
                        password_hash=hash_password(admin_password),
                        status="ACTIVE",
                        is_super_admin=False,
                        last_login_at_utc="",
                        failed_login_count=0,
                        locked_until_utc="",
                        session_revoked_at_utc="",
                        created_at_utc=now,
                    )
                )
                session.add(Organization(id=org_id, name="QVH", slug="qvh", status="ACTIVE", created_at_utc=now))
                session.commit()
                session.add(Workspace(id=ws_id, org_id=org_id, name="PAS EPR", slug="pas-epr", status="ACTIVE", created_at_utc=now))
                session.commit()
                session.add(Project(id=project_id, workspace_id=ws_id, name="PAS18.4 Migration", slug="pas18-4-migration", status="ACTIVE", created_at_utc=now))
                session.commit()
                session.add_all(
                    [
                        OrganizationMembership(user_id=super_id, org_id=org_id, role="super_admin", status="ACTIVE", created_at_utc=now),
                        OrganizationMembership(user_id=org_admin_id, org_id=org_id, role="org_admin", status="ACTIVE", created_at_utc=now),
                    ]
                )
                self._seed_role_permissions(session)
                session.commit()
            except IntegrityError:
                session.rollback()
                self._seed_role_permissions(session)
                session.commit()

    def _seed_role_permissions(self, session: Session) -> None:
        existing = {
            (row.role, row.permission)
            for row in session.scalars(select(RolePermission)).all()
        }
        for role, perms in DEFAULT_DMM_PERMISSIONS.items():
            for permission in perms:
                key = (role, permission)
                if key in existing:
                    continue
                session.add(RolePermission(role=role, permission=permission))

    def authenticate(self, username_or_email: str, password: str) -> Optional[Dict[str, object]]:
        ident = username_or_email.strip().lower()
        max_attempts = int(os.environ.get("DMM_AUTH_LOCK_MAX_ATTEMPTS", "5"))
        lock_minutes = int(os.environ.get("DMM_AUTH_LOCK_MINUTES", "15"))
        with self._session() as session:
            users = session.scalars(select(User)).all()
            for user in users:
                if ident not in {str(user.username).lower(), str(user.email).lower()}:
                    continue
                now = datetime.now(timezone.utc)
                if user.locked_until_utc and _to_epoch(user.locked_until_utc) > int(now.timestamp()):
                    user.status = "LOCKED"
                    session.commit()
                    return None
                if str(user.status).upper() != "ACTIVE":
                    return None
                if verify_password(password, user.password_hash):
                    user.failed_login_count = 0
                    user.locked_until_utc = ""
                    user.last_login_at_utc = now.isoformat()
                    session.commit()
                    return self._user_row(user)
                user.failed_login_count = int(user.failed_login_count or 0) + 1
                if int(user.failed_login_count) >= max_attempts:
                    user.status = "LOCKED"
                    user.locked_until_utc = (now + timedelta(minutes=lock_minutes)).isoformat()
                session.commit()
                return None
            return None

    def list_user_memberships(self, user_id: str) -> List[Dict[str, object]]:
        with self._session() as session:
            rows = session.execute(
                select(OrganizationMembership, Organization)
                .join(Organization, OrganizationMembership.org_id == Organization.id)
                .where(OrganizationMembership.user_id == user_id, OrganizationMembership.status == "ACTIVE")
            ).all()
            return [{"org_id": org.id, "org_name": org.name, "role": m.role} for m, org in rows]

    def list_orgs_for_user(self, user: Dict[str, object]) -> List[Dict[str, object]]:
        with self._session() as session:
            if user.get("is_super_admin"):
                rows = session.scalars(select(Organization)).all()
                return [self._org_row(r) for r in rows]
            memberships = session.scalars(
                select(OrganizationMembership).where(
                    OrganizationMembership.user_id == str(user.get("id", "")),
                    OrganizationMembership.status == "ACTIVE",
                )
            ).all()
            org_ids = {m.org_id for m in memberships}
            if not org_ids:
                return []
            rows = session.scalars(select(Organization).where(Organization.id.in_(org_ids))).all()
            return [self._org_row(r) for r in rows]

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, object]]:
        with self._session() as session:
            user = session.get(User, user_id)
            if not user:
                return None
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "status": user.status,
                "is_super_admin": bool(user.is_super_admin),
                "last_login_at_utc": user.last_login_at_utc,
                "failed_login_count": int(user.failed_login_count or 0),
                "locked_until_utc": user.locked_until_utc,
                "session_revoked_at_utc": user.session_revoked_at_utc,
                "created_at_utc": user.created_at_utc,
            }

    def user_has_org(self, user_id: str, org_id: str) -> bool:
        with self._session() as session:
            user = session.get(User, user_id)
            if not user:
                return False
            if user.is_super_admin:
                return True
            membership = session.scalar(
                select(OrganizationMembership.id).where(
                    OrganizationMembership.user_id == user_id,
                    OrganizationMembership.org_id == org_id,
                    OrganizationMembership.status == "ACTIVE",
                )
            )
            return bool(membership)

    def workspace_belongs_to_org(self, workspace_id: str, org_id: str) -> bool:
        with self._session() as session:
            hit = session.scalar(select(Workspace.id).where(Workspace.id == workspace_id, Workspace.org_id == org_id))
            return bool(hit)

    def project_belongs_to_workspace(self, project_id: str, workspace_id: str) -> bool:
        with self._session() as session:
            hit = session.scalar(select(Project.id).where(Project.id == project_id, Project.workspace_id == workspace_id))
            return bool(hit)

    def list_workspaces_for_org(self, org_id: str) -> List[Dict[str, object]]:
        with self._session() as session:
            rows = session.scalars(select(Workspace).where(Workspace.org_id == org_id)).all()
            return [self._workspace_row(r) for r in rows]

    def list_projects_for_workspace(self, workspace_id: str) -> List[Dict[str, object]]:
        with self._session() as session:
            rows = session.scalars(select(Project).where(Project.workspace_id == workspace_id)).all()
            return [self._project_row(r) for r in rows]

    def create_registration_request(self, username: str, email: str, display_name: str, password: str, requested_org_id: str) -> Dict[str, object]:
        with self._session() as session:
            org = session.get(Organization, requested_org_id)
            if not org:
                raise ValueError("requested organization not found")
            lower_username = username.strip().lower()
            lower_email = email.strip().lower()

            users = session.scalars(select(User)).all()
            if any(u.username.lower() == lower_username or u.email.lower() == lower_email for u in users):
                raise ValueError("username or email already exists")

            pending = session.scalars(select(RegistrationRequest).where(RegistrationRequest.status == "PENDING_APPROVAL")).all()
            if any(r.username.lower() == lower_username or r.email.lower() == lower_email for r in pending):
                raise ValueError("pending registration already exists")

            req = RegistrationRequest(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                display_name=display_name,
                password_hash=hash_password(password),
                requested_org_id=requested_org_id,
                status="PENDING_APPROVAL",
                reviewed_by="",
                reviewed_at_utc="",
                review_reason="",
                created_at_utc=_now(),
            )
            session.add(req)
            session.commit()
            return self._registration_row(req)

    def list_registration_requests(self, status: Optional[str] = None) -> List[Dict[str, object]]:
        with self._session() as session:
            stmt = select(RegistrationRequest)
            if status:
                stmt = stmt.where(RegistrationRequest.status == status.upper())
            rows = session.scalars(stmt).all()
            return [self._registration_row(r) for r in rows]

    def approve_registration(self, request_id: str, reviewer_user_id: str, role: str = "org_dm_engineer") -> Dict[str, object]:
        with self._session() as session:
            req = session.get(RegistrationRequest, request_id)
            if not req:
                raise ValueError("request not found")
            if req.status != "PENDING_APPROVAL":
                raise ValueError("request is not pending approval")

            now = _now()
            user = User(
                id=str(uuid.uuid4()),
                username=req.username,
                email=req.email,
                display_name=req.display_name,
                password_hash=req.password_hash,
                status="ACTIVE",
                is_super_admin=False,
                last_login_at_utc="",
                failed_login_count=0,
                locked_until_utc="",
                session_revoked_at_utc="",
                created_at_utc=now,
            )
            session.add(user)
            session.flush()
            session.add(
                OrganizationMembership(
                    user_id=user.id,
                    org_id=req.requested_org_id,
                    role=role,
                    status="ACTIVE",
                    created_at_utc=now,
                )
            )
            req.status = "APPROVED"
            req.reviewed_by = reviewer_user_id
            req.reviewed_at_utc = now
            session.commit()
            return {"request": self._registration_row(req), "user": self._user_row(user)}

    def reject_registration(self, request_id: str, reviewer_user_id: str, reason: str = "") -> Dict[str, object]:
        with self._session() as session:
            req = session.get(RegistrationRequest, request_id)
            if not req:
                raise ValueError("request not found")
            if req.status != "PENDING_APPROVAL":
                raise ValueError("request is not pending approval")
            req.status = "REJECTED"
            req.reviewed_by = reviewer_user_id
            req.reviewed_at_utc = _now()
            req.review_reason = reason
            session.commit()
            return self._registration_row(req)

    def create_org(self, name: str) -> Dict[str, object]:
        slug = _slugify(name)
        with self._session() as session:
            dup = session.scalar(select(Organization.id).where(Organization.slug == slug))
            if dup:
                raise ValueError("organization slug already exists")
            row = Organization(id=str(uuid.uuid4()), name=name, slug=slug, status="ACTIVE", created_at_utc=_now())
            session.add(row)
            session.commit()
            return self._org_row(row)

    def create_workspace(self, org_id: str, name: str) -> Dict[str, object]:
        slug = _slugify(name)
        with self._session() as session:
            org = session.get(Organization, org_id)
            if not org:
                raise ValueError("organization not found")
            row = Workspace(id=str(uuid.uuid4()), org_id=org_id, name=name, slug=slug, status="ACTIVE", created_at_utc=_now())
            session.add(row)
            session.commit()
            return self._workspace_row(row)

    def create_project(self, workspace_id: str, name: str) -> Dict[str, object]:
        slug = _slugify(name)
        with self._session() as session:
            ws = session.get(Workspace, workspace_id)
            if not ws:
                raise ValueError("workspace not found")
            row = Project(id=str(uuid.uuid4()), workspace_id=workspace_id, name=name, slug=slug, status="ACTIVE", created_at_utc=_now())
            session.add(row)
            session.commit()
            return self._project_row(row)

    def list_org_users(self, org_id: str) -> List[Dict[str, object]]:
        with self._session() as session:
            rows = session.execute(
                select(OrganizationMembership, User)
                .join(User, OrganizationMembership.user_id == User.id)
                .where(OrganizationMembership.org_id == org_id, OrganizationMembership.status == "ACTIVE")
            ).all()
            out = []
            for m, u in rows:
                out.append(
                    {
                        "user_id": u.id,
                        "username": u.username,
                        "email": u.email,
                        "display_name": u.display_name,
                        "role": m.role,
                        "status": u.status,
                    }
                )
            return out

    def list_permissions_for_role(self, role: str) -> List[str]:
        with self._session() as session:
            perms = session.scalars(select(RolePermission.permission).where(RolePermission.role == role)).all()
            if perms:
                return sorted(set(perms))
            return sorted(DEFAULT_DMM_PERMISSIONS.get(role, set()))

    def list_roles(self) -> List[str]:
        with self._session() as session:
            rows = session.scalars(select(RolePermission.role)).all()
            roles = set(str(r) for r in rows if str(r).strip())
            roles.update(DEFAULT_DMM_PERMISSIONS.keys())
            return sorted(roles)

    def list_users_with_memberships(self) -> List[Dict[str, object]]:
        with self._session() as session:
            users = session.scalars(select(User)).all()
            memberships = session.execute(
                select(OrganizationMembership, Organization)
                .join(Organization, OrganizationMembership.org_id == Organization.id)
            ).all()
            memberships_by_user: Dict[str, List[Dict[str, object]]] = {}
            for m, org in memberships:
                memberships_by_user.setdefault(m.user_id, []).append(
                    {
                        "org_id": org.id,
                        "org_name": org.name,
                        "role": m.role,
                        "status": m.status,
                        "created_at_utc": m.created_at_utc,
                    }
                )
            return [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "display_name": u.display_name,
                    "status": u.status,
                    "is_super_admin": bool(u.is_super_admin),
                    "last_login_at_utc": u.last_login_at_utc,
                    "failed_login_count": int(u.failed_login_count or 0),
                    "locked_until_utc": u.locked_until_utc,
                    "session_revoked_at_utc": u.session_revoked_at_utc,
                    "created_at_utc": u.created_at_utc,
                    "memberships": memberships_by_user.get(u.id, []),
                }
                for u in users
            ]

    def update_user_status(self, user_id: str, status: str) -> Dict[str, object]:
        status_norm = status.strip().upper()
        with self._session() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("user not found")
            user.status = status_norm
            session.commit()
            return self._user_row(user)

    def unlock_user(self, user_id: str) -> Dict[str, object]:
        with self._session() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("user not found")
            user.status = "ACTIVE"
            user.failed_login_count = 0
            user.locked_until_utc = ""
            session.commit()
            return self._user_row(user)

    def revoke_user_sessions(self, user_id: str) -> Dict[str, object]:
        with self._session() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("user not found")
            user.session_revoked_at_utc = _now()
            session.commit()
            return self._user_row(user)

    def is_token_revoked(self, user_id: str, token_iat: int) -> bool:
        with self._session() as session:
            user = session.get(User, user_id)
            if not user:
                return True
            return bool(user.session_revoked_at_utc and _to_epoch(user.session_revoked_at_utc) >= int(token_iat))

    def upsert_user_membership_role(self, user_id: str, org_id: str, role: str) -> Dict[str, object]:
        role_norm = role.strip()
        with self._session() as session:
            user = session.get(User, user_id)
            if not user:
                raise ValueError("user not found")
            org = session.get(Organization, org_id)
            if not org:
                raise ValueError("organization not found")
            if role_norm not in set(self.list_roles()):
                raise ValueError("unknown role")
            membership = session.scalar(
                select(OrganizationMembership).where(
                    OrganizationMembership.user_id == user_id,
                    OrganizationMembership.org_id == org_id,
                )
            )
            if membership:
                membership.role = role_norm
                membership.status = "ACTIVE"
            else:
                membership = OrganizationMembership(
                    user_id=user_id,
                    org_id=org_id,
                    role=role_norm,
                    status="ACTIVE",
                    created_at_utc=_now(),
                )
                session.add(membership)
            session.commit()
            return {
                "user_id": membership.user_id,
                "org_id": membership.org_id,
                "role": membership.role,
                "status": membership.status,
            }

    def remove_user_membership(self, user_id: str, org_id: str) -> Dict[str, object]:
        with self._session() as session:
            membership = session.scalar(
                select(OrganizationMembership).where(
                    OrganizationMembership.user_id == user_id,
                    OrganizationMembership.org_id == org_id,
                )
            )
            if not membership:
                raise ValueError("membership not found")
            membership.status = "DISABLED"
            session.commit()
            return {
                "user_id": membership.user_id,
                "org_id": membership.org_id,
                "role": membership.role,
                "status": membership.status,
            }

    def create_role(self, role: str, permissions: List[str]) -> Dict[str, object]:
        role_norm = role.strip()
        if not role_norm:
            raise ValueError("role is required")
        if role_norm in SYSTEM_DMM_ROLES:
            raise ValueError("cannot create reserved system role")
        perms = sorted({p.strip() for p in permissions if p.strip()})
        if not perms:
            raise ValueError("at least one permission is required")
        with self._session() as session:
            exists = session.scalar(select(RolePermission.id).where(RolePermission.role == role_norm))
            if exists:
                raise ValueError("role already exists")
            session.add_all([RolePermission(role=role_norm, permission=p) for p in perms])
            session.commit()
            return {"role": role_norm, "permissions": perms}

    def set_role_permissions(self, role: str, permissions: List[str]) -> Dict[str, object]:
        role_norm = role.strip()
        perms = sorted({p.strip() for p in permissions if p.strip()})
        if not perms:
            raise ValueError("at least one permission is required")
        with self._session() as session:
            exists = session.scalar(select(RolePermission.id).where(RolePermission.role == role_norm))
            if not exists:
                raise ValueError("role not found")
            session.execute(delete(RolePermission).where(RolePermission.role == role_norm))
            session.add_all([RolePermission(role=role_norm, permission=p) for p in perms])
            session.commit()
            return {"role": role_norm, "permissions": perms}

    def delete_role(self, role: str) -> Dict[str, object]:
        role_norm = role.strip()
        if role_norm in SYSTEM_DMM_ROLES:
            raise ValueError("cannot delete reserved system role")
        with self._session() as session:
            in_use = session.scalar(
                select(OrganizationMembership.id).where(
                    OrganizationMembership.role == role_norm,
                    OrganizationMembership.status == "ACTIVE",
                )
            )
            if in_use:
                raise ValueError("role is in use by active memberships")
            perms = session.scalars(select(RolePermission.permission).where(RolePermission.role == role_norm)).all()
            if not perms:
                raise ValueError("role not found")
            session.execute(delete(RolePermission).where(RolePermission.role == role_norm))
            session.commit()
            return {"role": role_norm, "permissions": sorted(set(perms))}

    @staticmethod
    def _user_row(user: User) -> Dict[str, object]:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "status": user.status,
            "is_super_admin": bool(user.is_super_admin),
            "last_login_at_utc": user.last_login_at_utc,
            "failed_login_count": int(user.failed_login_count or 0),
            "locked_until_utc": user.locked_until_utc,
            "session_revoked_at_utc": user.session_revoked_at_utc,
            "created_at_utc": user.created_at_utc,
        }

    @staticmethod
    def _org_row(row: Organization) -> Dict[str, object]:
        return {"id": row.id, "name": row.name, "slug": row.slug, "status": row.status, "created_at_utc": row.created_at_utc}

    @staticmethod
    def _workspace_row(row: Workspace) -> Dict[str, object]:
        return {
            "id": row.id,
            "org_id": row.org_id,
            "name": row.name,
            "slug": row.slug,
            "status": row.status,
            "created_at_utc": row.created_at_utc,
        }

    @staticmethod
    def _project_row(row: Project) -> Dict[str, object]:
        return {
            "id": row.id,
            "workspace_id": row.workspace_id,
            "name": row.name,
            "slug": row.slug,
            "status": row.status,
            "created_at_utc": row.created_at_utc,
        }

    @staticmethod
    def _registration_row(req: RegistrationRequest) -> Dict[str, object]:
        return {
            "id": req.id,
            "username": req.username,
            "email": req.email,
            "display_name": req.display_name,
            "password_hash": req.password_hash,
            "requested_org_id": req.requested_org_id,
            "status": req.status,
            "reviewed_by": req.reviewed_by,
            "reviewed_at_utc": req.reviewed_at_utc,
            "review_reason": req.review_reason,
            "created_at_utc": req.created_at_utc,
        }


class SaaSStore:
    def __init__(self, path: Path):
        backend = os.environ.get("DM_AUTH_BACKEND", "postgres").strip().lower()
        database_url = os.environ.get("DM_DATABASE_URL", "").strip()

        if backend == "file" or (backend == "postgres" and not database_url):
            self.impl = _FileSaaSStore(path)
        else:
            self.impl = _PostgresSaaSStore(database_url)

    def __getattr__(self, item):
        return getattr(self.impl, item)
