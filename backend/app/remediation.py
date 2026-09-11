"""Top Critical Vulnerabilities Remediation Engine & Fix Playbooks.

Provides concrete, engineer-ready fix approaches for the top 10 highest/P1 vulnerabilities:
- Root cause diagnosis
- Immediate virtual patch / WAF rule (zero-downtime mitigation)
- Permanent code/dependency patch
- Post-fix verification probe command
- Estimated engineering effort and liability saved
"""

from typing import Any, Dict, List, Optional


PLAYBOOK_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "CVE-2021-44228": {
        "title": "Log4j JNDI Remote Code Execution (Log4Shell)",
        "cwe": "CWE-502 / CWE-20",
        "root_cause": "Log4j jndi lookup plugin formats strings from untrusted input (User-Agent, headers) and executes arbitrary remote bytecode via LDAP/RMI.",
        "virtual_patch_waf": "SecRule REQUEST_HEADERS|REQUEST_BODY|ARGS \"(?i)\\$\\{jndi:(ldap|rmi|dns|nis):\" \"id:1001,phase:2,deny,status:403,msg:'Block Log4Shell JNDI Exploit'\"",
        "permanent_code_patch": """// pom.xml - Upgrade to log4j-core 2.17.1 or higher:
<dependency>
    <groupId>org.apache.logging.log4j</groupId>
    <artifactId>log4j-core</artifactId>
    <version>2.17.1</version>
</dependency>
// Or pass JVM runtime parameter:
// -Dlog4j2.formatMsgNoLookups=true""",
        "verification_probe": "curl -s -H 'X-Api-Probe: ${jndi:ldap://127.0.0.1:1389/a}' http://localhost:8080/ -o /dev/null -w '%{http_code}'",
        "expected_verification": "HTTP 403 or clean JSON without LDAP DNS callback",
        "estimated_hours": 1.5,
        "liability_saved_usd": 120000,
    },
    "CVE-2022-22965": {
        "title": "Spring Framework Data Binding RCE (Spring4Shell)",
        "cwe": "CWE-94",
        "root_cause": "Improper data binding access to getCachedIntrospectionResults() allows attacker to overwrite Tomcat AccessLogValve properties and upload a webshell.",
        "virtual_patch_waf": "SecRule ARGS_NAMES \"(?i)(class\\.module\\.classLoader|class\\.classLoader)\" \"id:1002,phase:2,deny,status:403,msg:'Block Spring4Shell ClassLoader Exploit'\"",
        "permanent_code_patch": """// build.gradle - Upgrade Spring Boot / Spring Framework:
implementation 'org.springframework.boot:spring-boot-starter-web:2.6.6' // or 2.7.0+
// Explicit WebDataBinder disallow fields in controller:
@InitBinder
public void setAllowedFields(WebDataBinder dataBinder) {
    String[] denylist = new String[]{\"class.*\", \"Class.*\", \"*.class.*\", \"*.Class.*\"};
    dataBinder.setDisallowedFields(denylist);
}""",
        "verification_probe": "curl -X POST -d 'class.module.classLoader.URLs[0]=0' http://localhost:8080/api/v1/user -w '%{http_code}'",
        "expected_verification": "HTTP 400 or HTTP 403 (Parameter binding rejected)",
        "estimated_hours": 2.0,
        "liability_saved_usd": 95000,
    },
    "CVE-2022-22963": {
        "title": "Spring Cloud Function SpEL Remote Code Execution",
        "cwe": "CWE-94",
        "root_cause": "RoutingFunction evaluates untrusted expressions passed in spring.cloud.function.routing-expression HTTP header as Spring Expression Language (SpEL).",
        "virtual_patch_waf": "SecRule REQUEST_HEADERS:spring.cloud.function.routing-expression \"@rx [\\(\\)\\[\\]\\$\\{\\}]\" \"id:1003,phase:1,deny,status:400,msg:'Block SpEL injection'\"",
        "permanent_code_patch": """// Upgrade spring-cloud-function-context to 3.1.7 or 3.2.3:
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-function-context</artifactId>
    <version>3.2.3</version>
</dependency>""",
        "verification_probe": "curl -X POST -H 'spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec(\"id\")' http://localhost:8080/functionRouter",
        "expected_verification": "HTTP 400 Bad Request",
        "estimated_hours": 1.0,
        "liability_saved_usd": 85000,
    },
    "CWE-89": {
        "title": "SQL Injection in User / Payment Query",
        "cwe": "CWE-89",
        "root_cause": "Raw user string concatenation directly into SQL query without parameterized prepared statements.",
        "virtual_patch_waf": "SecRule ARGS \"(?i)(union.*select|select.*from|drop.*table|insert.*into|1\\s*=\\s*1)\" \"id:1004,phase:2,deny,status:403,msg:'SQLi Attack'\"",
        "permanent_code_patch": """# Python/FastAPI SQLAlchemy example:
# VULNERABLE: db.execute(f"SELECT * FROM accounts WHERE id = '{user_id}'")
# PATCHED: Parameterized bind variable:
query = text("SELECT * FROM accounts WHERE id = :user_id")
result = db.execute(query, {"user_id": user_id}).fetchall()""",
        "verification_probe": "curl -s 'http://localhost:8000/api/v1/search?q=1%27+OR+%271%27=%271' | grep -i 'syntax error'",
        "expected_verification": "Zero SQL error leakage; sanitized empty result or validated 400 response",
        "estimated_hours": 1.5,
        "liability_saved_usd": 60000,
    },
    "CWE-918": {
        "title": "Server-Side Request Forgery (SSRF) in Webhook Dispatcher",
        "cwe": "CWE-918",
        "root_cause": "Application fetches remote URLs specified by user without validating against cloud metadata IP ranges (169.254.169.254) or internal private RFC1918 subnets.",
        "virtual_patch_waf": "SecRule ARGS:url \"(?i)(169\\.254|127\\.0\\.0|localhost|10\\.|192\\.168|metadata\\.google)\" \"id:1005,phase:2,deny,status:400,msg:'SSRF Private IP Block'\"",
        "permanent_code_patch": """import ipaddress
import urllib.parse

def is_safe_url(target_url: str) -> bool:
    parsed = urllib.parse.urlparse(target_url)
    if parsed.scheme not in ("http", "https"):
        return False
    # Resolve host and ensure it is not private/loopback/link-local:
    ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname))
    return not (ip.is_private or ip.is_loopback or ip.is_link_local)""",
        "verification_probe": "curl -X POST -H 'Content-Type: application/json' -d '{\"target\": \"http://169.254.169.254/latest/meta-data/\"}' http://localhost:8000/api/v1/webhook",
        "expected_verification": "HTTP 400 'Internal IP destinations forbidden'",
        "estimated_hours": 2.0,
        "liability_saved_usd": 75000,
    },
    "CWE-22": {
        "title": "Directory Traversal in File Download Handler",
        "cwe": "CWE-22",
        "root_cause": "Filename parameter from request is resolved using direct path joining without canonical base directory sandboxing.",
        "virtual_patch_waf": "SecRule ARGS \"(\\.\\./|\\.\\.\\\\)\" \"id:1006,phase:2,deny,status:403,msg:'Path Traversal Attempt'\"",
        "permanent_code_patch": """from pathlib import Path

BASE_DIR = Path("/var/app/static_files").resolve()

def get_safe_file_path(user_filename: str) -> Path:
    target_path = (BASE_DIR / user_filename).resolve()
    if not target_path.is_relative_to(BASE_DIR):
        raise PermissionError("Access Denied: Path traversal detected")
    return target_path""",
        "verification_probe": "curl -s 'http://localhost:8000/api/static?file=../../../../etc/passwd' -w '%{http_code}'",
        "expected_verification": "HTTP 403 Forbidden or HTTP 400 Bad Request",
        "estimated_hours": 1.0,
        "liability_saved_usd": 50000,
    },
    "CWE-798": {
        "title": "Hardcoded Cryptographic / API Secret in Source Code",
        "cwe": "CWE-798",
        "root_cause": "Sensitive JWT secret / HMAC signing key committed in plaintext in repository source code.",
        "virtual_patch_waf": "# Secret revocation: Invalidate current token signature and force key rotation",
        "permanent_code_patch": """# 1. Immediately revoke and rotate secret in Key Management Service (AWS KMS / HashiCorp Vault)
# 2. Retrieve secret dynamically from environment:
import os

JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise RuntimeError("CRITICAL: Strong JWT_SECRET_KEY environment variable is mandatory")""",
        "verification_probe": "git log -p -S 'hardcoded_secret_token' # Ensure secret is scrubbed from git history with git-filter-repo",
        "expected_verification": "Key rotated; zero plaintext secrets in repo tree",
        "estimated_hours": 1.0,
        "liability_saved_usd": 65000,
    },
    "CWE-79": {
        "title": "Cross-Site Scripting (XSS) in Dashboard Activity Log",
        "cwe": "CWE-79",
        "root_cause": "User-supplied payload rendered in innerHTML without HTML entity encoding or DOMPurify sanitization.",
        "virtual_patch_waf": "Header set Content-Security-Policy \"default-src 'self'; script-src 'self'; object-src 'none';\"",
        "permanent_code_patch": """// React / Next.js: Always use standard JSX text binding:
// VULNERABLE: <div dangerouslySetInnerHTML={{ __html: log.message }} />
// PATCHED:
import DOMPurify from 'dompurify';
<div>{log.message}</div> // standard JSX auto-escapes
// Or if HTML is required:
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(log.message) }} />""",
        "verification_probe": "curl -s 'http://localhost:3000/portal/activity?q=<script>alert(1)</script>' | grep -i '<script>alert'",
        "expected_verification": "Escaped as &lt;script&gt; or sanitized",
        "estimated_hours": 1.0,
        "liability_saved_usd": 35000,
    },
}


def get_remediation_for_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Generates an actionable remediation playbook for a given case."""
    vuln = case.get("vulnerability", {})
    title = case.get("title", "")
    cve = vuln.get("cve")
    cwe = vuln.get("cwe")
    priority = case.get("priority", {}).get("level", "P1")
    cost_burn = case.get("cost_burn", {})

    # Try matching by CVE
    playbook = None
    if cve and cve in PLAYBOOK_KNOWLEDGE_BASE:
        playbook = PLAYBOOK_KNOWLEDGE_BASE[cve]
    elif cwe and cwe in PLAYBOOK_KNOWLEDGE_BASE:
        playbook = PLAYBOOK_KNOWLEDGE_BASE[cwe]
    else:
        # Match by keywords in title
        t_lower = title.lower()
        if "log4j" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CVE-2021-44228"]
        elif "spring4shell" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CVE-2022-22965"]
        elif "spel" in t_lower or "spring cloud" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CVE-2022-22963"]
        elif "sql" in t_lower or "injection" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CWE-89"]
        elif "ssrf" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CWE-918"]
        elif "traversal" in t_lower or "path" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CWE-22"]
        elif "secret" in t_lower or "jwt" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CWE-798"]
        elif "xss" in t_lower:
            playbook = PLAYBOOK_KNOWLEDGE_BASE["CWE-79"]
        else:
            # Generic structured playbook
            playbook = {
                "title": f"Hardening Playbook: {title}",
                "cwe": cwe or "CWE-General",
                "root_cause": f"Vulnerability detected in {vuln.get('location') or 'target component'} via {vuln.get('scanner', 'scanner')}.",
                "virtual_patch_waf": f"# Implement ingress WAF rule restricting malicious request patterns to {vuln.get('location') or '/api'}",
                "permanent_code_patch": f"# 1. Upgrade affected package to latest secure patch\n# 2. Add input validation boundary around {vuln.get('location') or 'target'}\n# 3. Add unit test asserting patch integrity",
                "verification_probe": f"curl -s -X GET 'http://localhost:8000{vuln.get('location') or '/'}' -w '%{{http_code}}'",
                "expected_verification": "HTTP 200 / 400 with strict validation",
                "estimated_hours": 2.0,
                "liability_saved_usd": 45000,
            }

    return {
        "case_id": case.get("case_id"),
        "cluster_id": case.get("cluster_id"),
        "title": title,
        "cve": cve or "N/A",
        "cwe": cwe or "N/A",
        "priority": priority,
        "target_asset": case.get("asset", {}).get("asset_id") or case.get("asset", {}).get("hostname"),
        "daily_burn": cost_burn.get("formatted_daily", "$24,500/day"),
        "root_cause": playbook["root_cause"],
        "virtual_patch_waf": playbook["virtual_patch_waf"],
        "permanent_code_patch": playbook["permanent_code_patch"],
        "verification_probe": playbook["verification_probe"],
        "expected_verification": playbook["expected_verification"],
        "estimated_hours": playbook["estimated_hours"],
        "liability_saved_usd": playbook["liability_saved_usd"],
        "formatted_savings": f"${playbook['liability_saved_usd']:,.0f}",
    }


def get_top_p1_remediation_playbooks(cases: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """Filters top P1/highest severity cases and generates prioritized remediation playbooks."""
    # Priority sorting: P1 first, then by score descending
    def sort_key(c: Dict[str, Any]):
        p_val = {"P1": 4, "P2": 3, "P3": 2, "P4": 1}.get(c.get("priority", {}).get("level", "P2"), 2)
        score = c.get("priority", {}).get("score", 50.0)
        return (p_val, score)

    sorted_cases = sorted(cases, key=sort_key, reverse=True)
    top_cases = sorted_cases[:limit]

    playbooks = [get_remediation_for_case(c) for c in top_cases]
    return playbooks
