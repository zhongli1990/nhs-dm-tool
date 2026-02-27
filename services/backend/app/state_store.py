import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from sqlalchemy import Boolean, Float, Integer, String, Text, UniqueConstraint, create_engine, delete, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from .services.artifact_service import read_json


Base = declarative_base()


class MappingWorkbenchRecord(Base):
    __tablename__ = "mapping_workbench"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workbench_id: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    target_table: Mapped[str] = mapped_column(String(256), index=True)
    target_field: Mapped[str] = mapped_column(String(256), index=True)
    mapping_class: Mapped[str] = mapped_column(String(128), default="")
    primary_source_table: Mapped[str] = mapped_column(String(256), default="")
    primary_source_field: Mapped[str] = mapped_column(String(256), default="")
    transformation_rule: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(64), default="DRAFT", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    last_updated_by: Mapped[str] = mapped_column(String(128), default="system")
    last_updated_at_utc: Mapped[str] = mapped_column(String(64), default=lambda: datetime.now(timezone.utc).isoformat())


class QualityHistoryRecord(Base):
    __tablename__ = "quality_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts_utc: Mapped[str] = mapped_column(String(64), index=True)
    event: Mapped[str] = mapped_column(String(128), default="")
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    crosswalk_rejects: Mapped[int] = mapped_column(Integer, default=0)
    population_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    tables_written: Mapped[int] = mapped_column(Integer, default=0)
    unresolved_mapping: Mapped[int] = mapped_column(Integer, default=0)
    release_status: Mapped[str] = mapped_column(String(64), default="UNKNOWN")


class QualityKpiConfigRecord(Base):
    __tablename__ = "quality_kpi_config"
    __table_args__ = (UniqueConstraint("kpi_id", name="uq_quality_kpi_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kpi_id: Mapped[str] = mapped_column(String(128), index=True)
    label: Mapped[str] = mapped_column(String(256))
    threshold: Mapped[float] = mapped_column(Float, default=0.0)
    direction: Mapped[str] = mapped_column(String(16), default="max")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    format: Mapped[str] = mapped_column(String(16), default="int")


class RuntimeStateStore:
    def __init__(
        self,
        backend: str,
        database_url: str,
        mapping_workbench_file: Path,
        quality_history_file: Path,
        quality_kpi_config_file: Path,
    ):
        self.backend = backend.strip().lower()
        self.mapping_workbench_file = mapping_workbench_file
        self.quality_history_file = quality_history_file
        self.quality_kpi_config_file = quality_kpi_config_file

        self.session_factory = None
        if self.backend == "postgres" and database_url:
            engine = create_engine(database_url, pool_pre_ping=True)
            Base.metadata.create_all(engine)
            self.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        else:
            self.backend = "file"

    def _session(self) -> Session:
        if not self.session_factory:
            raise RuntimeError("postgres backend not configured")
        return self.session_factory()

    def read_workbench(self) -> List[Dict[str, object]]:
        if self.backend == "file":
            if not self.mapping_workbench_file.exists():
                return []
            payload = read_json(self.mapping_workbench_file)
            if not payload:
                try:
                    raw = self.mapping_workbench_file.read_text(encoding="utf-8")
                    end = raw.rfind("]")
                    if end > 0:
                        repaired = json.loads(raw[: end + 1])
                        if isinstance(repaired, list):
                            self.mapping_workbench_file.write_text(json.dumps(repaired, indent=2), encoding="utf-8")
                            payload = repaired
                except Exception:
                    payload = {}
            return payload if isinstance(payload, list) else []

        with self._session() as session:
            rows = session.scalars(select(MappingWorkbenchRecord).order_by(MappingWorkbenchRecord.target_table, MappingWorkbenchRecord.target_field)).all()
            return [self._workbench_row(r) for r in rows]

    def write_workbench(self, rows: List[Dict[str, object]]) -> None:
        if self.backend == "file":
            self.mapping_workbench_file.parent.mkdir(parents=True, exist_ok=True)
            self.mapping_workbench_file.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            return

        with self._session() as session:
            session.execute(delete(MappingWorkbenchRecord))
            for row in rows:
                session.add(
                    MappingWorkbenchRecord(
                        workbench_id=str(row.get("workbench_id", "")),
                        target_table=str(row.get("target_table", "")),
                        target_field=str(row.get("target_field", "")),
                        mapping_class=str(row.get("mapping_class", "")),
                        primary_source_table=str(row.get("primary_source_table", "")),
                        primary_source_field=str(row.get("primary_source_field", "")),
                        transformation_rule=str(row.get("transformation_rule", "")),
                        status=str(row.get("status", "DRAFT")),
                        notes=str(row.get("notes", "")),
                        last_updated_by=str(row.get("last_updated_by", "system")),
                        last_updated_at_utc=str(row.get("last_updated_at_utc", datetime.now(timezone.utc).isoformat())),
                    )
                )
            session.commit()

    def read_quality_history(self) -> List[Dict[str, object]]:
        if self.backend == "file":
            if not self.quality_history_file.exists():
                return []
            payload = read_json(self.quality_history_file)
            return payload if isinstance(payload, list) else []

        with self._session() as session:
            rows = session.scalars(select(QualityHistoryRecord).order_by(QualityHistoryRecord.id.asc())).all()
            return [self._quality_history_row(r) for r in rows]

    def write_quality_history(self, rows: List[Dict[str, object]]) -> None:
        rows = rows[-300:]
        if self.backend == "file":
            self.quality_history_file.parent.mkdir(parents=True, exist_ok=True)
            self.quality_history_file.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            return

        with self._session() as session:
            session.execute(delete(QualityHistoryRecord))
            for row in rows:
                session.add(
                    QualityHistoryRecord(
                        ts_utc=str(row.get("ts_utc", datetime.now(timezone.utc).isoformat())),
                        event=str(row.get("event", "")),
                        error_count=int(row.get("error_count", 0) or 0),
                        warning_count=int(row.get("warning_count", 0) or 0),
                        crosswalk_rejects=int(row.get("crosswalk_rejects", 0) or 0),
                        population_ratio=float(row.get("population_ratio", 0) or 0),
                        tables_written=int(row.get("tables_written", 0) or 0),
                        unresolved_mapping=int(row.get("unresolved_mapping", 0) or 0),
                        release_status=str(row.get("release_status", "UNKNOWN")),
                    )
                )
            session.commit()

    def read_quality_kpis(self, default_rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
        if self.backend == "file":
            if not self.quality_kpi_config_file.exists():
                self.write_quality_kpis(default_rows)
                return default_rows
            payload = read_json(self.quality_kpi_config_file)
            rows = payload if isinstance(payload, list) else []
            return rows or default_rows

        with self._session() as session:
            rows = session.scalars(select(QualityKpiConfigRecord).order_by(QualityKpiConfigRecord.id.asc())).all()
            if not rows:
                self.write_quality_kpis(default_rows)
                return default_rows
            return [self._quality_kpi_row(r) for r in rows]

    def write_quality_kpis(self, rows: List[Dict[str, object]]) -> None:
        if self.backend == "file":
            self.quality_kpi_config_file.parent.mkdir(parents=True, exist_ok=True)
            self.quality_kpi_config_file.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            return

        with self._session() as session:
            session.execute(delete(QualityKpiConfigRecord))
            for row in rows:
                session.add(
                    QualityKpiConfigRecord(
                        kpi_id=str(row.get("id", "")),
                        label=str(row.get("label", "")),
                        threshold=float(row.get("threshold", 0) or 0),
                        direction="min" if str(row.get("direction", "max")).lower() == "min" else "max",
                        enabled=bool(row.get("enabled", True)),
                        format="pct" if str(row.get("format", "int")).lower() == "pct" else "int",
                    )
                )
            session.commit()

    @staticmethod
    def _workbench_row(r: MappingWorkbenchRecord) -> Dict[str, object]:
        return {
            "workbench_id": r.workbench_id,
            "target_table": r.target_table,
            "target_field": r.target_field,
            "mapping_class": r.mapping_class,
            "primary_source_table": r.primary_source_table,
            "primary_source_field": r.primary_source_field,
            "transformation_rule": r.transformation_rule,
            "status": r.status,
            "notes": r.notes,
            "last_updated_by": r.last_updated_by,
            "last_updated_at_utc": r.last_updated_at_utc,
        }

    @staticmethod
    def _quality_history_row(r: QualityHistoryRecord) -> Dict[str, object]:
        return {
            "ts_utc": r.ts_utc,
            "event": r.event,
            "error_count": r.error_count,
            "warning_count": r.warning_count,
            "crosswalk_rejects": r.crosswalk_rejects,
            "population_ratio": r.population_ratio,
            "tables_written": r.tables_written,
            "unresolved_mapping": r.unresolved_mapping,
            "release_status": r.release_status,
        }

    @staticmethod
    def _quality_kpi_row(r: QualityKpiConfigRecord) -> Dict[str, object]:
        return {
            "id": r.kpi_id,
            "label": r.label,
            "threshold": r.threshold,
            "direction": r.direction,
            "enabled": r.enabled,
            "format": r.format,
        }
