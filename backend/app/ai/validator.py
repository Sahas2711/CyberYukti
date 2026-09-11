import json
import re
from datetime import datetime, timezone
from typing import Optional

from .schemas import AIAnalysis

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)
CWE_PATTERN = re.compile(r"CWE-\d+", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\b")

SCHEMA_FIELDS = {
    "summary",
    "why_it_matters",
    "evidence_summary",
    "priority_explanation",
    "investigation_questions",
    "recommended_remediation",
    "confidence_notes",
    "limitations",
    "model",
    "generated_at",
    "grounded_on",
}

LIST_FIELDS = {
    "investigation_questions",
    "recommended_remediation",
    "confidence_notes",
    "limitations",
    "grounded_on",
}


def _extract_json(raw: str) -> Optional[dict]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _check_required_fields(data: dict) -> list[str]:
    errors: list[str] = []
    for field in SCHEMA_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    return errors


def _check_list_types(data: dict) -> list[str]:
    errors: list[str] = []
    for field in LIST_FIELDS:
        if field in data and not isinstance(data[field], list):
            errors.append(f"Field '{field}' must be a list")
    return errors


def _check_grounding(data: dict, case: dict) -> list[str]:
    warnings: list[str] = []
    ground_fields = ["summary", "why_it_matters", "priority_explanation"]

    case_text_parts = []
    if "title" in case:
        case_text_parts.append(str(case["title"]))
    if "vulnerability" in case and isinstance(case["vulnerability"], dict):
        vuln = case["vulnerability"]
        for key in ("title", "description", "severity", "cvss_score", "epss_percentile"):
            if key in vuln:
                case_text_parts.append(str(vuln[key]))
    if "cluster_id" in case:
        case_text_parts.append(str(case["cluster_id"]))

    case_text = " ".join(case_text_parts).lower()
    case_numbers = set(NUMBER_PATTERN.findall(case_text))

    for field in ground_fields:
        if field in data and isinstance(data[field], str):
            ai_numbers = set(NUMBER_PATTERN.findall(data[field]))
            for num in ai_numbers:
                if num not in case_numbers:
                    warnings.append(
                        f"Number '{num}' in '{field}' not found in input case data"
                    )

    ai_cves = set()
    for field in ground_fields:
        if field in data and isinstance(data[field], str):
            ai_cves.update(CVE_PATTERN.findall(data[field]))

    input_cves = set()
    for field in ["cve", "description", "title"]:
        if field in case and isinstance(case[field], str):
            input_cves.update(CVE_PATTERN.findall(case[field]))
    if "vulnerability" in case and isinstance(case["vulnerability"], dict):
        for sub in ["cve", "description", "title"]:
            if sub in case["vulnerability"] and isinstance(case["vulnerability"][sub], str):
                input_cves.update(CVE_PATTERN.findall(case["vulnerability"][sub]))

    for cve in ai_cves:
        if cve.upper() not in {c.upper() for c in input_cves}:
            warnings.append(f"Referenced CVE '{cve}' not found in input case data")

    return warnings


def _check_cve_cwe(data: dict) -> list[str]:
    warnings: list[str] = []
    for field in ["summary", "why_it_matters", "evidence_summary"]:
        if field in data and isinstance(data[field], str):
            cves = CVE_PATTERN.findall(data[field])
            cwes = CWE_PATTERN.findall(data[field])
            for cwe in cwes:
                warnings.append(f"Referenced {cwe} in '{field}' — verify against input data")
    return warnings


def _check_evidence_refs(data: dict) -> list[str]:
    warnings: list[str] = []
    grounded = data.get("grounded_on", [])
    if isinstance(grounded, list) and len(grounded) == 0:
        warnings.append("grounded_on is empty — analysis should reference input fields")
    return warnings


def _parse_analysis(raw_output: str) -> Optional[AIAnalysis]:
    data = _extract_json(raw_output)
    if data is None:
        return None
    try:
        return AIAnalysis(**data)
    except Exception:
        return None


def validate_analysis(
    raw_output: str, case: dict
) -> tuple[Optional[AIAnalysis], list[str]]:
    errors: list[str] = []
    data = _extract_json(raw_output)

    if data is None:
        errors.append("Failed to parse JSON from model output")
        return None, errors

    errors.extend(_check_required_fields(data))
    errors.extend(_check_list_types(data))

    warnings: list[str] = []
    warnings.extend(_check_grounding(data, case))
    warnings.extend(_check_cve_cwe(data))
    warnings.extend(_check_evidence_refs(data))

    all_issues = errors + warnings
    if errors:
        return None, all_issues

    try:
        analysis = AIAnalysis(**data)
    except Exception as e:
        all_issues.append(f"Pydantic validation failed: {e}")
        return None, all_issues

    if not analysis.generated_at:
        analysis.generated_at = datetime.now(timezone.utc).isoformat()

    return analysis, all_issues
