"""FastAPI Server for Evidence Validation Engine.

Implements /validate, /health, /probes endpoints with strict adherence
to the Section 25 error contract and security boundaries.
"""

import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

try:
    from config import MAX_PAYLOAD_SIZE_BYTES
    from models import (
        CanonicalFinding,
        ExecutionAudit,
        InvalidInputException,
        ProbeAudit,
        SecurityViolationException,
        ValidationResult,
        ValidationStatus,
    )
    from validator.evaluator import evaluate
    from validator.registry import (
        get_registered_probes,
        select_probe_for_finding,
    )
    from validator.target_registry import resolve_target
except ImportError:
    from ..config import MAX_PAYLOAD_SIZE_BYTES
    from ..models import (
        CanonicalFinding,
        ExecutionAudit,
        InvalidInputException,
        ProbeAudit,
        SecurityViolationException,
        ValidationResult,
        ValidationStatus,
    )
    from ..validator.evaluator import evaluate
    from ..validator.registry import (
        get_registered_probes,
        select_probe_for_finding,
    )
    from ..validator.target_registry import resolve_target

app = FastAPI(
    title="Evidence Validation Engine API",
    version="1.0.0",
    description="Deterministic, zero-LLM security vulnerability evidence validation service",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors as per Section 25 Error Contract."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "malformed_input", "detail": str(exc)},
    )


@app.exception_handler(InvalidInputException)
async def invalid_input_handler(request: Request, exc: InvalidInputException):
    """Handle rejected adversarial inputs as per Section 25 Error Contract."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "invalid_probe_request", "detail": exc.detail},
    )


@app.exception_handler(SecurityViolationException)
async def security_violation_handler(request: Request, exc: SecurityViolationException):
    """Handle security violations as per Section 25 Error Contract."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "invalid_probe_request", "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Sanitized 500 error handler: never leaks stack traces."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error"},
    )


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/probes")
def list_probes() -> Dict[str, Any]:
    """Return list of available safe probes."""
    return {"probes": get_registered_probes()}


@app.post("/validate", response_model=ValidationResult)
async def validate_finding(request: Request):
    """Validate a canonical security finding against allowlisted lab targets.

    Deterministic pipeline: Target resolution -> Probe selection -> Safe execution -> Deterministic evaluation.
    """
    start_time = time.perf_counter()

    # 1. Payload size guardrail (Section 25: 413 for oversized payloads)
    body_bytes = await request.body()
    if len(body_bytes) > MAX_PAYLOAD_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"error": "payload_too_large"},
        )

    # 2. Parse and check for malformed JSON
    try:
        raw_json = json.loads(body_bytes.decode("utf-8"))
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "malformed_input", "detail": f"Malformed JSON: {str(exc)}"},
        )

    if not isinstance(raw_json, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "malformed_input", "detail": "Request body must be a JSON object."},
        )

    # 3. Adversarial and probe override checks (Section 25 / Section 27a)
    # Reject attempts to smuggle arbitrary executable commands or override probes
    dangerous_keys = {"command", "cmd", "exec", "script", "probe_override", "payload"}
    for key in dangerous_keys:
        if key in raw_json:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_probe_request",
                    "detail": f"Forbidden field '{key}' detected. Arbitrary command injection is strictly prohibited.",
                },
            )

    # Check if request attempts to specify an unknown/unregistered probe type explicitly
    if "probe" in raw_json:
        probe_val = raw_json["probe"]
        probe_type = probe_val.get("type") if isinstance(probe_val, dict) else str(probe_val)
        if probe_type and probe_type not in get_registered_probes():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_probe_request",
                    "detail": f"Explicitly requested probe '{probe_type}' is unknown or unregistered.",
                },
            )

    # 4. Schema validation into CanonicalFinding
    try:
        finding = CanonicalFinding.model_validate(raw_json)
    except ValidationError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "malformed_input", "detail": str(exc)},
        )

    validation_id = f"V-{uuid.uuid4().hex[:8]}"

    # 5. Target resolution guardrail (Section 6a / Section 25)
    # If asset.id is not in registry, return 200 with status: INCONCLUSIVE
    asset_id = finding.asset.id
    target_config = resolve_target(asset_id)
    if not target_config:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ValidationResult(
            finding_id=finding.finding_id,
            status=ValidationStatus.INCONCLUSIVE,
            confidence=0.10,
            observed={},
            probe=ProbeAudit(type="UNKNOWN", version="1.0", status="SKIPPED"),
            execution=ExecutionAudit(sandbox="docker", duration_ms=duration_ms),
            reason=[
                f"Asset '{asset_id}' is not in the controlled lab target registry",
                "Unregistered targets cannot be probed for safety and SSRF boundaries",
            ],
            validation_id=validation_id,
        )

    # 6. Deterministic probe selection (Section 17 / Section 25)
    # If location.type is not mapped, return 200 with status: INCONCLUSIVE
    selected = select_probe_for_finding(finding)
    if not selected:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ValidationResult(
            finding_id=finding.finding_id,
            status=ValidationStatus.INCONCLUSIVE,
            confidence=0.30,
            observed={},
            probe=ProbeAudit(type="NONE", version="1.0", status="UNSUPPORTED"),
            execution=ExecutionAudit(sandbox="docker", duration_ms=duration_ms),
            reason=[
                f"No safe validation probe mapped for location type '{finding.location.type}'",
                "Finding evidence claim cannot be independently confirmed",
            ],
            validation_id=validation_id,
        )

    probe_name, probe_func = selected

    # 7. Execute probe under guardrails
    try:
        exec_status, observed_data, error_detail = probe_func(finding, target_config)
    except InvalidInputException as exc:
        # Input sanitization failure inside probe (e.g. metacharacters, path traversal, unauthorized port)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_probe_request", "detail": exc.detail},
        )
    except Exception as exc:
        exec_status = "ERROR"
        observed_data = {}
        error_detail = f"Unexpected probe failure: {str(exc)}"

    # 8. Deterministic Evaluation (Section 21)
    custom_reasons = [error_detail] if error_detail else []
    val_status, confidence, reasons = evaluate(
        expected=finding.evidence,
        observed=observed_data,
        execution_status=exec_status,
        probe_type=probe_name,
        custom_reasons=custom_reasons,
    )

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    probe_run_status = "PASS" if exec_status == "SUCCESS" else "FAIL"
    return ValidationResult(
        finding_id=finding.finding_id,
        status=val_status,
        confidence=confidence,
        observed=observed_data,
        probe=ProbeAudit(type=probe_name, version="1.0", status=probe_run_status),
        execution=ExecutionAudit(sandbox="docker", duration_ms=max(1, duration_ms)),
        reason=reasons,
        validation_id=validation_id,
    )
