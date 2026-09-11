import re

MAX_STRING_LENGTH = 2000
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

UNTRUSTED_FIELDS: list[str] = [
    "title",
    "description",
    "raw_evidence",
    "cve",
    "cwe",
    "scanner",
    "scanner_rule_id",
    "hostname",
    "environment",
    "criticality",
    "observed_at",
    "summary",
    "why_it_matters",
    "evidence_summary",
    "priority_explanation",
    "investigation_questions",
    "recommended_remediation",
    "confidence_notes",
    "limitations",
    "level",
    "status",
    "actor",
    "action",
    "reason",
]

ASSET_FIELDS: list[str] = [
    "hostname",
    "environment",
    "criticality",
]


def sanitize_string(field_name: str, value: str) -> str:
    cleaned = CONTROL_CHAR_RE.sub("", value)
    if len(cleaned) > MAX_STRING_LENGTH:
        cleaned = cleaned[:MAX_STRING_LENGTH]
    return f'<UNTRUSTED field="{field_name}">{cleaned}</UNTRUSTED>'


def sanitize_case_for_llm(case: dict) -> dict:
    sanitized: dict = {}
    for key, value in case.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_dict_fields(key, value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(key, item)
                if isinstance(item, str) and key in UNTRUSTED_FIELDS
                else item
                for item in value
            ]
        elif isinstance(value, str) and key in UNTRUSTED_FIELDS:
            sanitized[key] = sanitize_string(key, value)
        else:
            sanitized[key] = value
    return sanitized


def sanitize_dict_fields(parent_key: str, data: dict) -> dict:
    sanitized: dict = {}
    for key, value in data.items():
        qualified = f"{parent_key}.{key}"
        if isinstance(value, str) and (key in UNTRUSTED_FIELDS or key in ASSET_FIELDS):
            sanitized[key] = sanitize_string(qualified, value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_fields(qualified, value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(qualified, item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized
