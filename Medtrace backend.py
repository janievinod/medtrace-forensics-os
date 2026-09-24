from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.engine import Engine


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/medtrace"
)
engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(api_key_header)) -> None:
    """Protect the prototype API; configure a long random key before starting it."""
    expected = os.getenv("MEDTRACE_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="Server is not configured: set MEDTRACE_API_KEY.")
    if api_key is None or not __import__("hmac").compare_digest(api_key, expected):
        raise HTTPException(status_code=401, detail="A valid X-API-Key header is required.")


app = FastAPI(
    title="MEDTRACE API",
    description="EHR activity monitoring, anomaly detection, investigation, and integrity API.",
    version="1.0.0",
    dependencies=[Depends(require_api_key)],
)


class AccessLogCreate(BaseModel):
    session_id: int | None = None
    user_id: int
    patient_id: int
    device_id: int | None = None
    access_type: Literal["view", "create", "update", "delete", "export", "print"]
    table_accessed: str = "patient_records"
    record_id: str | None = None
    access_time: datetime | None = None
    success: bool = True
    ip_address: str | None = None
    notes: str | None = None


class AnomalyStatusUpdate(BaseModel):
    status: Literal["open", "investigating", "closed", "false_positive"]


class InvestigationCreate(BaseModel):
    opened_by: int
    assigned_to: int | None = None
    summary: str | None = None
    anomaly_ids: list[int] = Field(default_factory=list)


class InvestigationStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "closed"]
    summary: str | None = None


class EvidenceCreate(BaseModel):
    log_id: int | None = None
    evidence_type: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1)
    collected_by: int | None = None


class ForensicReportCreate(BaseModel):
    generated_by: int | None = None
    findings: str = Field(min_length=1)
    conclusion: str | None = None


class IntegrityCheckCreate(BaseModel):
    patient_id: int | None = None
    table_name: str = Field(min_length=1, max_length=100)
    record_id: str = Field(min_length=1, max_length=50)
    original_hash: str = Field(min_length=1, max_length=128)
    current_hash: str = Field(min_length=1, max_length=128)
    hash_algorithm: str = Field(default="SHA-256", max_length=20)
    verified_by: int | None = None


def query(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Run a read query and return JSON-serializable row mappings."""
    try:
        with engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(sql), params or {}).mappings().all()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database query failed; check DATABASE_URL and schema setup.") from exc


def mutate(sql: str, params: dict[str, Any] | None = None, *, returning: bool = True) -> Any:
    """Run one transaction; row constraints and foreign keys stay enforced by PostgreSQL."""
    try:
        with engine.begin() as conn:
            result = conn.execute(text(sql), params or {})
            if returning:
                row = result.mappings().first()
                return dict(row) if row else None
            return {"updated": result.rowcount}
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="The request conflicts with a database constraint or referenced ID.") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database operation failed; check DATABASE_URL and schema setup.") from exc


def audit(conn, actor_user_id: int | None, action: str, target_table: str, target_id: Any, details: dict[str, Any] | None = None) -> None:
    conn.execute(text("""INSERT INTO audit_log (actor_user_id, action, target_table, target_id, details)
                        VALUES (:actor, :action, :table, :id, CAST(:details AS jsonb))"""), {
        "actor": actor_user_id, "action": action, "table": target_table,
        "id": str(target_id) if target_id is not None else None,
        "details": __import__("json").dumps(details or {}),
    })


@app.get("/", tags=["system"])
def root():
    return {"service": "MEDTRACE API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["system"])
def health():
    query("SELECT 1 AS database_connected")
    return {"status": "ok", "database": "connected"}


@app.get("/api/dashboard", tags=["analytics"])
def dashboard():
    rows = query("""SELECT
        (SELECT COUNT(*) FROM ehr_access_logs WHERE access_time >= now() - interval '24 hours') AS accesses_24h,
        (SELECT COUNT(*) FROM anomalies WHERE status IN ('open','investigating')) AS active_anomalies,
        (SELECT COUNT(*) FROM investigations WHERE status IN ('open','in_progress')) AS active_investigations,
        (SELECT COUNT(*) FROM integrity_checks WHERE integrity_status = 'tampered') AS tampered_records,
        (SELECT COUNT(*) FROM devices WHERE is_trusted = FALSE) AS untrusted_devices""")
    return {"summary": rows[0], "top_risks": query("SELECT * FROM v_suspicious_activity LIMIT 10")}


@app.get("/api/users", tags=["directory"])
def list_users(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return query("""SELECT u.user_id, u.username, u.full_name, u.email, u.role_id, r.role_name,
                         u.department_id, d.department_name, u.employee_code, u.is_active, u.created_at
                  FROM users u JOIN roles r USING (role_id) LEFT JOIN departments d USING (department_id)
                  ORDER BY u.user_id LIMIT :limit OFFSET :offset""", {"limit": limit, "offset": offset})


@app.get("/api/patients", tags=["directory"])
def list_patients(q: str | None = None, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return query("""SELECT patient_id, mrn, full_name, date_of_birth, gender, primary_department_id, created_at
                  FROM patients WHERE (:q IS NULL OR full_name ILIKE :pattern OR mrn ILIKE :pattern)
                  ORDER BY patient_id LIMIT :limit OFFSET :offset""",
                 {"q": q, "pattern": f"%{q}%" if q else None, "limit": limit, "offset": offset})


@app.get("/api/devices", tags=["directory"])
def list_devices():
    return query("SELECT * FROM v_device_activity")


@app.get("/api/logs", tags=["activity"])
def list_logs(user_id: int | None = None, patient_id: int | None = None,
              start: datetime | None = None, end: datetime | None = None,
              limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return query("""SELECT l.*, u.full_name AS user_name, p.mrn, p.full_name AS patient_name,
                         d.device_name, d.is_trusted
                  FROM ehr_access_logs l JOIN users u USING (user_id)
                  JOIN patients p USING (patient_id) LEFT JOIN devices d USING (device_id)
                  WHERE (:user_id IS NULL OR l.user_id = :user_id)
                    AND (:patient_id IS NULL OR l.patient_id = :patient_id)
                    AND (:start IS NULL OR l.access_time >= :start)
                    AND (:end IS NULL OR l.access_time < :end)
                  ORDER BY l.access_time DESC, l.log_id DESC LIMIT :limit OFFSET :offset""",
                 {"user_id": user_id, "patient_id": patient_id, "start": start, "end": end, "limit": limit, "offset": offset})


@app.post("/api/logs", status_code=status.HTTP_201_CREATED, tags=["activity"])
def create_log(payload: AccessLogCreate):
    fields = payload.model_dump(exclude_none=True)
    cols = ", ".join(fields)
    binds = ", ".join(f":{key}" for key in fields)
    with engine.begin() as conn:
        try:
            row = conn.execute(text(f"INSERT INTO ehr_access_logs ({cols}) VALUES ({binds}) RETURNING *"), fields).mappings().one()
            return dict(row)
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Referenced user, patient, device, or session does not exist.") from exc
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="Database operation failed; check DATABASE_URL and schema setup.") from exc


@app.get("/api/analytics/user-risk", tags=["analytics"])
def user_risk():
    return query("SELECT * FROM v_user_risk_summary")


@app.get("/api/analytics/device-activity", tags=["analytics"])
def device_activity():
    return query("SELECT * FROM v_device_activity")


@app.get("/api/anomalies", tags=["anomalies"])
def list_anomalies(status_filter: str | None = Query(None, alias="status"), risk_level: str | None = None,
                   user_id: int | None = None, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return query("""SELECT a.*, rs.risk_score, rs.risk_level, rs.scoring_reason,
                         u.full_name AS user_name, e.description AS event_description
                  FROM anomalies a LEFT JOIN risk_scores rs USING (anomaly_id)
                  JOIN users u USING (user_id) LEFT JOIN events e USING (event_id)
                  WHERE (:status IS NULL OR a.status::text = :status)
                    AND (:risk IS NULL OR rs.risk_level::text = :risk)
                    AND (:user_id IS NULL OR a.user_id = :user_id)
                  ORDER BY rs.risk_score DESC NULLS LAST, a.detected_at DESC
                  LIMIT :limit OFFSET :offset""",
                 {"status": status_filter, "risk": risk_level, "user_id": user_id, "limit": limit, "offset": offset})


@app.get("/api/anomalies/{anomaly_id}", tags=["anomalies"])
def get_anomaly(anomaly_id: int):
    rows = query("""SELECT a.*, rs.risk_score, rs.risk_level, rs.scoring_reason,
                         u.full_name AS user_name, e.description AS event_description
                  FROM anomalies a LEFT JOIN risk_scores rs USING (anomaly_id)
                  JOIN users u USING (user_id) LEFT JOIN events e USING (event_id)
                  WHERE a.anomaly_id = :id""", {"id": anomaly_id})
    if not rows:
        raise HTTPException(404, "Anomaly not found")
    return rows[0]


@app.patch("/api/anomalies/{anomaly_id}/status", tags=["anomalies"])
def update_anomaly_status(anomaly_id: int, payload: AnomalyStatusUpdate):
    with engine.begin() as conn:
        row = conn.execute(text("UPDATE anomalies SET status = CAST(:status AS anomaly_status_enum) WHERE anomaly_id = :id RETURNING *"),
                           {"status": payload.status, "id": anomaly_id}).mappings().first()
        if not row:
            raise HTTPException(404, "Anomaly not found")
        audit(conn, None, "update_anomaly_status", "anomalies", anomaly_id, {"status": payload.status})
        return dict(row)


@app.get("/api/investigations", tags=["investigations"])
def list_investigations(status_filter: str | None = Query(None, alias="status"), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return query("""SELECT i.*, opener.full_name AS opened_by_name, assignee.full_name AS assigned_to_name,
                         COUNT(ia.anomaly_id)::int AS anomaly_count
                  FROM investigations i JOIN users opener ON opener.user_id=i.opened_by
                  LEFT JOIN users assignee ON assignee.user_id=i.assigned_to
                  LEFT JOIN investigation_anomalies ia USING (investigation_id)
                  WHERE (:status IS NULL OR i.status::text = :status)
                  GROUP BY i.investigation_id, opener.full_name, assignee.full_name
                  ORDER BY i.opened_at DESC LIMIT :limit OFFSET :offset""",
                 {"status": status_filter, "limit": limit, "offset": offset})


@app.post("/api/investigations", status_code=201, tags=["investigations"])
def create_investigation(payload: InvestigationCreate):
    try:
        with engine.begin() as conn:
            row = conn.execute(text("""INSERT INTO investigations (opened_by, assigned_to, summary)
                                       VALUES (:opened_by, :assigned_to, :summary) RETURNING *"""),
                               payload.model_dump(exclude={"anomaly_ids"})).mappings().one()
            investigation = dict(row)
            for anomaly_id in payload.anomaly_ids:
                conn.execute(text("INSERT INTO investigation_anomalies (investigation_id, anomaly_id) VALUES (:iid, :aid)"),
                             {"iid": investigation["investigation_id"], "aid": anomaly_id})
            audit(conn, payload.opened_by, "create_investigation", "investigations", investigation["investigation_id"], {"anomaly_ids": payload.anomaly_ids})
            return investigation
    except IntegrityError as exc:
        raise HTTPException(409, "An opener, assignee, or anomaly ID does not exist, or an anomaly was linked twice.") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Database operation failed; check DATABASE_URL and schema setup.") from exc


@app.patch("/api/investigations/{investigation_id}/status", tags=["investigations"])
def update_investigation(investigation_id: int, payload: InvestigationStatusUpdate):
    with engine.begin() as conn:
        row = conn.execute(text("""UPDATE investigations SET status=CAST(:status AS investigation_status_enum),
                    summary=COALESCE(:summary, summary),
                    closed_at=CASE WHEN :status='closed' THEN COALESCE(closed_at, now()) ELSE NULL END
                    WHERE investigation_id=:id RETURNING *"""),
                           {"status": payload.status, "summary": payload.summary, "id": investigation_id}).mappings().first()
        if not row:
            raise HTTPException(404, "Investigation not found")
        audit(conn, None, "update_investigation_status", "investigations", investigation_id, {"status": payload.status})
        return dict(row)


@app.get("/api/investigations/{investigation_id}/timeline", tags=["investigations"])
def investigation_timeline(investigation_id: int):
    exists = query("SELECT 1 FROM investigations WHERE investigation_id=:id", {"id": investigation_id})
    if not exists:
        raise HTTPException(404, "Investigation not found")
    return query("SELECT * FROM v_investigation_timeline WHERE investigation_id=:id ORDER BY event_time", {"id": investigation_id})


@app.get("/api/investigations/{investigation_id}/evidence", tags=["investigations"])
def list_evidence(investigation_id: int):
    return query("SELECT * FROM evidence WHERE investigation_id=:id ORDER BY collected_at", {"id": investigation_id})


@app.post("/api/investigations/{investigation_id}/evidence", status_code=201, tags=["investigations"])
def add_evidence(investigation_id: int, payload: EvidenceCreate):
    return mutate("""INSERT INTO evidence (investigation_id, log_id, evidence_type, description, collected_by)
                    VALUES (:iid, :log_id, :evidence_type, :description, :collected_by) RETURNING *""",
                  {"iid": investigation_id, **payload.model_dump()})


@app.get("/api/investigations/{investigation_id}/report", tags=["investigations"])
def get_forensic_report(investigation_id: int):
    rows = query("SELECT * FROM forensic_reports WHERE investigation_id=:id", {"id": investigation_id})
    if not rows:
        raise HTTPException(404, "Forensic report not found")
    return rows[0]


@app.put("/api/investigations/{investigation_id}/report", tags=["investigations"])
def upsert_forensic_report(investigation_id: int, payload: ForensicReportCreate):
    return mutate("""INSERT INTO forensic_reports (investigation_id, generated_by, findings, conclusion, report_hash)
                    VALUES (:iid, :generated_by, :findings, :conclusion,
                            encode(digest(:findings || COALESCE(:conclusion,''), 'sha256'),'hex'))
                    ON CONFLICT (investigation_id) DO UPDATE SET generated_by=EXCLUDED.generated_by,
                    generated_at=now(), findings=EXCLUDED.findings, conclusion=EXCLUDED.conclusion,
                    report_hash=EXCLUDED.report_hash RETURNING *""",
                  {"iid": investigation_id, **payload.model_dump()})


@app.get("/api/integrity-checks", tags=["integrity"])
def integrity_checks(integrity_status: str | None = None, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return query("""SELECT * FROM v_integrity_status
                  WHERE (:state IS NULL OR integrity_status::text=:state)
                  ORDER BY verification_time DESC LIMIT :limit OFFSET :offset""",
                 {"state": integrity_status, "limit": limit, "offset": offset})


@app.post("/api/integrity-checks", status_code=201, tags=["integrity"])
def create_integrity_check(payload: IntegrityCheckCreate):
    integrity_state = "verified" if payload.original_hash == payload.current_hash else "tampered"
    return mutate("""INSERT INTO integrity_checks (patient_id, table_name, record_id, hash_algorithm,
                    original_hash, current_hash, integrity_status, verified_by)
                    VALUES (:patient_id, :table_name, :record_id, :algorithm, :original_hash,
                    :current_hash, CAST(:state AS integrity_status_enum), :verified_by) RETURNING *""",
                  {"patient_id": payload.patient_id, "table_name": payload.table_name, "record_id": payload.record_id,
                   "algorithm": payload.hash_algorithm, "original_hash": payload.original_hash,
                   "current_hash": payload.current_hash, "state": integrity_state, "verified_by": payload.verified_by})


@app.get("/api/sessions", tags=["activity"])
def list_sessions(user_id: int | None = None, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return query("""SELECT s.*, u.full_name AS user_name, d.device_name, d.is_trusted
                  FROM sessions s JOIN users u USING (user_id) LEFT JOIN devices d USING (device_id)
                  WHERE (:user_id IS NULL OR s.user_id=:user_id)
                  ORDER BY login_time DESC LIMIT :limit OFFSET :offset""",
                 {"user_id": user_id, "limit": limit, "offset": offset})


@app.get("/api/events", tags=["activity"])
def list_events(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return query("""SELECT e.*, u.full_name AS user_name, d.department_name,
                         COUNT(el.log_id)::int AS linked_log_count
                  FROM events e LEFT JOIN users u USING(user_id) LEFT JOIN departments d USING(department_id)
                  LEFT JOIN event_logs el USING(event_id) GROUP BY e.event_id, u.full_name, d.department_name
                  ORDER BY e.event_time DESC LIMIT :limit OFFSET :offset""", {"limit": limit, "offset": offset})
