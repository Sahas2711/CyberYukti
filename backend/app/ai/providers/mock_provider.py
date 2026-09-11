import json
import re
from datetime import datetime, timezone

from ..provider import LLMProvider

TAG_RE = re.compile(r"<UNTRUSTED[^>]*>(.*?)</UNTRUSTED>", re.DOTALL)


def _clean(value: str) -> str:
    if not isinstance(value, str):
        return value
    return TAG_RE.sub(lambda m: m.group(1), value)


class MockProvider(LLMProvider):
    def analyze(self, case: dict) -> str:
        title = _clean(case.get("title", "Unknown vulnerability"))
        cluster_id = case.get("cluster_id", "unknown")
        case_id = _clean(case.get("case_id", "unknown"))
        finding_count = case.get("finding_count", 1)

        asset = case.get("asset", {})
        hostname = _clean(asset.get("hostname", "unknown-host")) if isinstance(asset, dict) else "unknown-host"
        environment = _clean(asset.get("environment", "production")) if isinstance(asset, dict) else "production"
        internet_exposed = asset.get("internet_exposed", False) if isinstance(asset, dict) else False

        vulnerability = case.get("vulnerability", {})
        cve = _clean(vulnerability.get("cve", None)) if isinstance(vulnerability, dict) else None
        cwe = _clean(vulnerability.get("cwe", None)) if isinstance(vulnerability, dict) else None

        priority = case.get("priority", {})
        priority_level = _clean(priority.get("level", "MEDIUM")) if isinstance(priority, dict) else "MEDIUM"
        priority_score = priority.get("score", 5.0) if isinstance(priority, dict) else 5.0

        evidence = case.get("evidence", {})
        evidence_status = _clean(evidence.get("status", "UNVALIDATED")) if isinstance(evidence, dict) else "UNVALIDATED"
        evidence_confidence = evidence.get("confidence", None) if isinstance(evidence, dict) else None

        threat_intel = case.get("threat_intelligence", {})
        vuln_cvss = vulnerability.get("cvss_score", None) if isinstance(vulnerability, dict) else None
        cvss = threat_intel.get("cvss", vuln_cvss) if isinstance(threat_intel, dict) else vuln_cvss
        epss = threat_intel.get("epss", None) if isinstance(threat_intel, dict) else None
        kev = threat_intel.get("kev", None) if isinstance(threat_intel, dict) else None

        cve_ref = f" (related to {cve})" if cve else ""
        cwe_ref = f" ({cwe})" if cwe else ""
        cvss_ref = f" with CVSS {cvss}" if cvss else ""
        exposure_ref = " internet-facing" if internet_exposed else ""

        summary = (
            f"Case {case_id}: {title}{cve_ref}. "
            f"This{exposure_ref} {environment} asset ({hostname}) is affected. "
            f"Priority level: {priority_level} (score {priority_score}). "
            f"Cluster contains {finding_count} finding(s). "
            f"Evidence validation status: {evidence_status}."
        )

        article = "an" if internet_exposed else "a"
        why_it_matters = (
            f"This vulnerability{cve_ref}{cwe_ref}{cvss_ref} on {article}{exposure_ref} {environment} "
            f"system ({hostname}) poses risk to the organization. "
            f"With priority {priority_level} ({priority_score}/100), "
            f"{'immediate' if priority_level in ('P1', 'CRITICAL') else 'timely'} "
            f"remediation is recommended."
        )

        evidence_summary = (
            f"Evidence validation status: {evidence_status}"
            f"{f' with confidence {evidence_confidence}' if evidence_confidence is not None else ''}. "
            f"The vulnerability was detected on host {hostname} in {environment} environment."
        )

        priority_explanation = (
            f"Priority {priority_level} (score {priority_score}) is based on the "
            f"asset criticality ({asset.get('criticality', 'unknown') if isinstance(asset, dict) else 'unknown'}), "
            f"{'internet exposure' if internet_exposed else 'internal network placement'}, "
            f"threat intelligence factors{cvss_ref}"
            f"{f' (EPSS {epss})' if epss is not None else ''}"
            f"{', and KEV listing' if kev else ''}."
        )

        investigation_questions = [
            f"Is {hostname} currently running the vulnerable component?",
            f"Are there compensating controls in place for {environment} systems?",
            "Has exploitation been observed in the wild for this vulnerability?",
            f"What is the patch availability for this issue on {hostname}?",
        ]

        recommended_remediation = [
            f"Apply available patches to {hostname} in {environment}",
            "Implement network segmentation if immediate patching is not possible",
            "Review firewall rules for internet-facing assets",
            "Schedule a focused vulnerability scan after remediation",
        ]

        confidence_notes = [
            f"Evidence validation: {evidence_status}"
            + (f" ({evidence_confidence})" if evidence_confidence is not None else ""),
            f"Asset criticality: {asset.get('criticality', 'unknown') if isinstance(asset, dict) else 'unknown'}",
            f"Internet exposed: {internet_exposed}",
        ]

        limitations = [
            "Analysis is based on automated data collection and may not reflect the full operational context",
            "Remediation recommendations are generic and should be adapted to local change management processes",
        ]

        grounded_on = [
            "case.title",
            "case.vulnerability",
            "case.asset",
            "case.evidence",
            "case.priority",
            "case.threat_intelligence",
        ]

        analysis = {
            "summary": summary,
            "why_it_matters": why_it_matters,
            "evidence_summary": evidence_summary,
            "priority_explanation": priority_explanation,
            "investigation_questions": investigation_questions,
            "recommended_remediation": recommended_remediation,
            "confidence_notes": confidence_notes,
            "limitations": limitations,
            "model": "mock-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "grounded_on": grounded_on,
        }

        return json.dumps(analysis)
