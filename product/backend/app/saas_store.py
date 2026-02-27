import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .security import hash_password, verify_password


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")


class SaaSStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self._seed_data())

    def _seed_data(self) -> Dict[str, object]:
        org_id = str(uuid.uuid4())
        ws_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        super_id = str(uuid.uuid4())
        org_admin_id = str(uuid.uuid4())
        return {
            "users": [
                {
                    "id": super_id,
                    "username": "superadmin",
                    "email": "superadmin@openli.local",
                    "display_name": "OpenLI Super Admin",
                    "password_hash": hash_password("Admin@123"),
                    "status": "ACTIVE",
                    "is_super_admin": True,
                    "created_at_utc": _now(),
                },
                {
                    "id": org_admin_id,
                    "username": "qvh_admin",
                    "email": "qvh.admin@openli.local",
                    "display_name": "QVH Org Admin",
                    "password_hash": hash_password("Admin@123"),
                    "status": "ACTIVE",
                    "is_super_admin": False,
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
        with self.lock:
            data = self._read()
            for user in data["users"]:
                if user.get("status") != "ACTIVE":
                    continue
                if username_or_email.lower() in {str(user.get("username", "")).lower(), str(user.get("email", "")).lower()}:
                    if verify_password(password, str(user.get("password_hash", ""))):
                        return user
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
            for w in data["workspaces"]:
                if w.get("id") == workspace_id and w.get("org_id") == org_id:
                    return True
            return False

    def project_belongs_to_workspace(self, project_id: str, workspace_id: str) -> bool:
        with self.lock:
            data = self._read()
            for p in data["projects"]:
                if p.get("id") == project_id and p.get("workspace_id") == workspace_id:
                    return True
            return False

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
            existing_users = {(u.get("username", "").lower(), u.get("email", "").lower()) for u in data["users"]}
            if any(username.lower() == u[0] or email.lower() == u[1] for u in existing_users):
                raise ValueError("username or email already exists")
            for req in data["registration_requests"]:
                if req.get("status") == "PENDING_APPROVAL" and (req.get("username", "").lower() == username.lower() or req.get("email", "").lower() == email.lower()):
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
            req = None
            for row in data["registration_requests"]:
                if row.get("id") == request_id:
                    req = row
                    break
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
