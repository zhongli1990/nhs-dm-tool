import json
import os
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import Integer, String, Text, create_engine, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker


Base = declarative_base()


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at_utc: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    outcome: Mapped[str] = mapped_column(String(32), index=True)

    actor_user_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    actor_role: Mapped[str] = mapped_column(String(64), default="", index=True)
    actor_org_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    actor_workspace_id: Mapped[str] = mapped_column(String(64), default="")
    actor_project_id: Mapped[str] = mapped_column(String(64), default="")

    target_type: Mapped[str] = mapped_column(String(64), default="", index=True)
    target_id: Mapped[str] = mapped_column(String(128), default="", index=True)

    request_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    request_ip: Mapped[str] = mapped_column(String(128), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")

    details_json: Mapped[str] = mapped_column(Text, default="{}")


class AuditStore:
    def __init__(self, backend: str, database_url: str):
        self.backend = backend.strip().lower()
        self.enabled = os.environ.get("DM_AUDIT_ENABLED", "true").strip().lower() in {"1", "true", "yes"}
        self.session_factory = None

        if not self.enabled:
            return

        if self.backend == "postgres" and database_url:
            engine = create_engine(database_url, pool_pre_ping=True)
            if os.environ.get("DM_SCHEMA_AUTOCREATE", "false").strip().lower() in {"1", "true", "yes"}:
                Base.metadata.create_all(engine)
            self.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        else:
            self.backend = "disabled"

    def _session(self) -> Session:
        if not self.session_factory:
            raise RuntimeError("audit store is not configured")
        return self.session_factory()

    def record(
        self,
        *,
        event_type: str,
        outcome: str,
        actor_user_id: str = "",
        actor_role: str = "",
        actor_org_id: str = "",
        actor_workspace_id: str = "",
        actor_project_id: str = "",
        target_type: str = "",
        target_id: str = "",
        request_id: str = "",
        request_ip: str = "",
        user_agent: str = "",
        details: Optional[Dict[str, object]] = None,
    ) -> None:
        if not self.enabled or self.backend != "postgres":
            return
        try:
            with self._session() as session:
                session.add(
                    AuditEvent(
                        created_at_utc=datetime.now(timezone.utc).isoformat(),
                        event_type=str(event_type)[:128],
                        outcome=str(outcome).upper()[:32],
                        actor_user_id=str(actor_user_id)[:64],
                        actor_role=str(actor_role)[:64],
                        actor_org_id=str(actor_org_id)[:64],
                        actor_workspace_id=str(actor_workspace_id)[:64],
                        actor_project_id=str(actor_project_id)[:64],
                        target_type=str(target_type)[:64],
                        target_id=str(target_id)[:128],
                        request_id=str(request_id)[:128],
                        request_ip=str(request_ip)[:128],
                        user_agent=str(user_agent),
                        details_json=json.dumps(details or {}, ensure_ascii=True),
                    )
                )
                session.commit()
        except Exception:
            print("[DMM][WARN] audit log write failed")
            traceback.print_exc()

    def list_events(
        self,
        *,
        limit: int = 200,
        event_type: str = "",
        outcome: str = "",
        actor_org_id: str = "",
    ) -> List[Dict[str, object]]:
        if not self.enabled or self.backend != "postgres":
            return []

        limit = max(1, min(int(limit), 2000))
        with self._session() as session:
            stmt = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
            if event_type:
                stmt = stmt.where(AuditEvent.event_type == event_type)
            if outcome:
                stmt = stmt.where(AuditEvent.outcome == outcome.upper())
            if actor_org_id:
                stmt = stmt.where(AuditEvent.actor_org_id == actor_org_id)
            rows = session.scalars(stmt).all()
            return [self._row(r) for r in rows]

    @staticmethod
    def _row(r: AuditEvent) -> Dict[str, object]:
        details: Dict[str, object] = {}
        try:
            parsed = json.loads(r.details_json or "{}")
            if isinstance(parsed, dict):
                details = parsed
        except Exception:
            details = {}

        return {
            "id": r.id,
            "created_at_utc": r.created_at_utc,
            "event_type": r.event_type,
            "outcome": r.outcome,
            "actor_user_id": r.actor_user_id,
            "actor_role": r.actor_role,
            "actor_org_id": r.actor_org_id,
            "actor_workspace_id": r.actor_workspace_id,
            "actor_project_id": r.actor_project_id,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "request_id": r.request_id,
            "request_ip": r.request_ip,
            "user_agent": r.user_agent,
            "details": details,
        }
