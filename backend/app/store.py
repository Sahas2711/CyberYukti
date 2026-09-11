"""Shared in-memory case store.

Single source of truth for all API routes. Fixes person4's bug where
case_routes / ai_routes / dashboard_routes each held an independent
copy of the fixture dict (mutations were invisible across routes).

The store is hydrated from fixtures on startup, then enriched with real
pipeline data: clusters produced by the Person 1 ingestion engine
(3-tier dedup over real scanner fixtures) and risk scores computed by
the Person 3 scoring formula (severity/asset/exposure/validation).
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.mock.fixtures import CASES
from backend.app.ingestion.normalizer import FindingIntelligenceEngine
from backend.app.ingestion.models import IncidentCluster
from services.risk_engine.scoring import calculate_risk_score
from services.risk_engine.models import (
    AssetContext,
    FindingInput,
    ValidationResult as RiskValidationResult,
)

_LOCK = threading.RLock()

_cases_store: Dict[str, dict] = {}
_audit_store: Dict[str, List[dict]] = {}
_clusters_store: Dict[str, dict] = {}
_pipeline_meta: Dict[str, Any] = {
    "ingested": False,
    "summary": None,
    "source": "fixtures",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cluster_to_finding_input(cluster: IncidentCluster) -> FindingInput:
    """Map an IncidentCluster from the ingestion engine onto the
    risk-engine's FindingInput contract."""
    rep = cluster.representative_finding
    severity = (rep.raw_severity or "unknown").lower()
    if severity not in ("critical", "high", "medium", "low", "informational"):
        severity = "unknown"
    # Map the demo target asset onto an asset context. The ingestion
    # fixtures only carry a target string, so derive conservative context.
    internet_exposed = True  # DAST/SAST targets in the fixture are web-facing
    criticality = 0.8 if "critical" in (cluster.target_asset or "") else 0.6
    return FindingInput(
        finding_id=cluster.cluster_id,
        cluster_id=cluster.cluster_id,
        title=cluster.title,
        severity=severity,
        cve=cluster.primary_cve,
        cvss=None,
        asset=AssetContext(
            id=cluster.target_asset,
            criticality=criticality,
            internet_exposed=internet_exposed,
            environment="production",
        ),
        validation=RiskValidationResult(status="UNAVAILABLE", confidence=0.0),
    )


def _apply_ingestion_clusters() -> None:
    """Run the real ingestion engine over the scanner fixtures and overlay
    the resulting clusters' data onto matching cases (by CVE / component)."""
    engine = FindingIntelligenceEngine()
    base = None
    try:
        from backend.app.main import BASE_DIR  # avoid circular import at module load
        base = base or BASE_DIR
    except Exception:
        from pathlib import Path
        base = Path(__file__).resolve().parent.parent.parent

    fixtures_dir = base / "backend" / "fixtures" / "raw_scans"
    fixture_files = [
        fixtures_dir / "trivy_scan.json",
        fixtures_dir / "semgrep_scan.json",
        fixtures_dir / "nuclei_scan.json",
    ]
    existing = [f for f in fixture_files if f.exists()]
    if not existing:
        return

    try:
        clusters, summary = engine.process_raw_files([str(f) for f in existing])
    except Exception:
        return

    _pipeline_meta["ingested"] = True
    _pipeline_meta["summary"] = summary.model_dump()
    _pipeline_meta["source"] = "ingestion-engine"

    for cluster in clusters:
        _clusters_store[cluster.cluster_id] = cluster.model_dump()

    # Overlay cluster facts onto seeded cases: enrich sources and
    # finding counts where a case matches a cluster's CVE/component.
    for case in _cases_store.values():
        vuln = case.get("vulnerability", {})
        case_cve = vuln.get("cve")
        for cdump in _clusters_store.values():
            rep = cdump.get("representative_finding", {})
            same_cve = case_cve and cdump.get("primary_cve") == case_cve
            same_component = (
                rep.get("package_name")
                and rep.get("package_name") in (case.get("title") or "").lower()
            )
            if same_cve or same_component:
                tools = cdump.get("participating_tools", [])
                merged = list(dict.fromkeys((case.get("sources") or []) + tools))
                case["sources"] = merged
                case["finding_count"] = max(
                    case.get("finding_count", 1), cdump.get("raw_findings_count", 1)
                )
                case["pipeline_cluster_id"] = cdump.get("cluster_id")


def _recompute_priorities() -> None:
    """Recompute every case's priority using the real Person 3 scoring
    formula instead of hardcoded fixture scores."""
    for case in _cases_store.values():
        try:
            validation = case.get("evidence", {})
            finding = FindingInput(
                finding_id=case["case_id"],
                cluster_id=case.get("cluster_id"),
                title=case.get("title", ""),
                severity=_severity_from_case(case),
                cve=case.get("vulnerability", {}).get("cve"),
                cvss=case.get("threat_intelligence", {}).get("cvss"),
                asset=AssetContext(
                    id=case["asset"].get("asset_id", "unknown"),
                    criticality=_criticality_to_float(case["asset"].get("criticality")),
                    internet_exposed=bool(case["asset"].get("internet_exposed")),
                    environment=_normalize_env(case["asset"].get("environment")),
                ),
                validation=RiskValidationResult(
                    status=validation.get("status", "UNAVAILABLE"),
                    confidence=float(validation.get("confidence", 0.0)),
                ),
            )
            result = calculate_risk_score(finding)
            case["priority"] = {
                "cluster_id": case.get("cluster_id", case["case_id"]),
                "score": round(result.risk_score * 100, 1),
                "level": result.priority,
                "factors": result.factors,
                "formula_version": "risk-engine-1.0.0",
            }
        except Exception:
            # Never let scoring failures break the API; keep fixture score.
            continue


def _severity_from_case(case: dict) -> str:
    cvss = case.get("threat_intelligence", {}).get("cvss")
    if cvss is not None:
        if cvss >= 9.0:
            return "critical"
        if cvss >= 7.0:
            return "high"
        if cvss >= 4.0:
            return "medium"
        return "low"
    return "unknown"


def _criticality_to_float(criticality: Any) -> float:
    mapping = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
    if isinstance(criticality, (int, float)):
        return float(criticality)
    return mapping.get(str(criticality).lower(), 0.5)


def _normalize_env(env: Any) -> str:
    mapping = {"production": "production", "staging": "staging", "dev": "development"}
    return mapping.get(str(env).lower(), "unknown")


def init_store() -> None:
    """Hydrate the store from fixtures, then enrich with real pipeline data."""
    with _LOCK:
        if _cases_store:
            return
        for case in CASES:
            dumped = case if isinstance(case, dict) else case.model_dump()
            _cases_store[case["case_id"] if isinstance(case, dict) else case.case_id] = dumped
        _apply_ingestion_clusters()
        _recompute_priorities()


def ensure_audit(case_id: str) -> List[dict]:
    with _LOCK:
        if case_id not in _audit_store:
            _audit_store[case_id] = []
        return _audit_store[case_id]


def add_audit_event(
    case_id: str,
    actor: str,
    actor_id: Optional[str],
    action: str,
    previous_state: Optional[dict],
    new_state: Optional[dict],
    metadata: Optional[dict] = None,
) -> dict:
    import uuid

    audit = ensure_audit(case_id)
    with _LOCK:
        event = {
            "event_id": str(uuid.uuid4()),
            "case_id": case_id,
            "timestamp": _now_iso(),
            "actor": actor,
            "actor_id": actor_id,
            "action": action,
            "previous_state": previous_state,
            "new_state": new_state,
            "metadata": metadata,
            "prev_hash": audit[-1]["event_id"] if audit else None,
        }
        audit.append(event)
    return event


def get_cases() -> List[dict]:
    with _LOCK:
        return list(_cases_store.values())


def get_case(case_id: str) -> Optional[dict]:
    with _LOCK:
        return _cases_store.get(case_id)


def get_pipeline_meta() -> Dict[str, Any]:
    with _LOCK:
        return dict(_pipeline_meta)


def get_clusters() -> List[dict]:
    with _LOCK:
        return list(_clusters_store.values())


def validate_case_live(case_id: str, target_override: Optional[str] = None) -> Optional[dict]:
    """Execute live validation probe for a case and dynamically update priority and audit trail."""
    with _LOCK:
        case = _cases_store.get(case_id)
        if not case:
            return None

        from backend.app.validator_bridge import execute_case_validation

        prev_evidence = dict(case.get("evidence", {}))
        prev_priority = dict(case.get("priority", {}))

        # Execute live probe against controlled lab target
        live_evidence = execute_case_validation(case, target_override)
        case["evidence"] = live_evidence

        # Recalculate priority dynamically based on fresh evidence status
        _recompute_priorities()

        # Record audit event
        add_audit_event(
            case_id=case_id,
            actor="evidence-engine",
            actor_id="validator-live",
            action="EVIDENCE_VALIDATED",
            previous_state={
                "evidence_status": prev_evidence.get("status"),
                "priority": prev_priority.get("level"),
                "score": prev_priority.get("score"),
            },
            new_state={
                "evidence_status": live_evidence.get("status"),
                "priority": case.get("priority", {}).get("level"),
                "score": case.get("priority", {}).get("score"),
            },
            metadata={
                "confidence": live_evidence.get("confidence"),
                "reasons": live_evidence.get("reasons", []),
                "target": target_override or case.get("asset", {}).get("asset_id"),
            },
        )
        return case

