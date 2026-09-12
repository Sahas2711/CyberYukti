"""
Generates a plain, zero-saturation, information-dense architecture diagram for CyberYukti (PS16).
Designed strictly for technical clarity and readability:
- High contrast, neutral grayscale and technical slate palette (no saturated colors)
- Standard Draw.io / Eraser / Lucidchart / Whitepaper engineering styling
- Focus on technical information, deterministic pipeline stages, formulas, and dataflows
"""

import os
import subprocess

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CyberYukti PS16 System Architecture</title>
<style>
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  body {
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    background: #ffffff;
    /* Subtle plain diagram tool dot grid */
    background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
    background-size: 20px 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #0f172a;
    position: relative;
    user-select: none;
  }

  /* Header - Engineering Title Block */
  .header {
    position: absolute;
    top: 18px;
    left: 0;
    width: 1920px;
    text-align: center;
  }
  .header h1 {
    font-size: 28px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
  }
  .header h2 {
    font-size: 15px;
    font-weight: 600;
    color: #475569;
    margin-top: 3px;
    letter-spacing: 0.2px;
  }

  /* SVG Overlay for Connectors */
  svg.connectors {
    position: absolute;
    top: 0;
    left: 0;
    width: 1920px;
    height: 1080px;
    pointer-events: none;
    z-index: 10;
  }

  /* Standard Plain Technical Diagram Box */
  .diag-box {
    position: absolute;
    background: #ffffff;
    border: 1.5px solid #1e293b;
    border-radius: 6px;
    z-index: 20;
    display: flex;
    flex-direction: column;
    padding: 12px 14px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }
  .diag-title {
    font-size: 15px;
    font-weight: 800;
    color: #0f172a;
    text-align: center;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
  }
  .diag-subtitle {
    font-size: 11.5px;
    font-weight: 600;
    color: #64748b;
    text-align: center;
    margin-top: -2px;
    margin-bottom: 8px;
  }

  /* Untrusted Boundary Frame */
  .untrusted-boundary {
    position: absolute;
    left: 75px;
    top: 86px;
    width: 345px;
    height: 250px;
    border: 1.5px dashed #475569;
    border-radius: 6px;
    background: #f8fafc;
    z-index: 5;
  }
  .untrusted-tag {
    position: absolute;
    width: 100%;
    text-align: center;
    font-size: 11px;
    font-weight: 800;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }
  .untrusted-tag.top { top: -18px; }
  .untrusted-tag.bottom { bottom: -18px; }

  /* Sub-item white node card */
  .diag-node {
    background: #f8fafc;
    border: 1px solid #94a3b8;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 11.5px;
    font-weight: 700;
    color: #0f172a;
    text-align: center;
  }

  /* Scanner item cards */
  .scanner-grid {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    gap: 8px;
  }
  .scanner-item {
    background: #ffffff;
    border: 1px solid #94a3b8;
    border-radius: 4px;
    padding: 10px 8px;
    text-align: center;
    flex: 1;
  }
  .scanner-name {
    font-size: 12px;
    font-weight: 800;
    color: #0f172a;
  }
  .scanner-type {
    font-size: 10.5px;
    color: #475569;
    font-weight: 700;
  }

  /* Parser items in Ingestion */
  .parser-col {
    display: flex;
    flex-direction: column;
    gap: 7px;
    width: 170px;
  }
  .canonical-cylinder {
    background: #f8fafc;
    border: 1.5px solid #1e293b;
    border-radius: 6px;
    padding: 10px;
    width: 135px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .canonical-text {
    font-size: 12px;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.25;
  }

  /* Probes grid */
  .probes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    width: 440px;
  }
  .probe-pill {
    background: #ffffff;
    border: 1px solid #64748b;
    border-radius: 4px;
    padding: 7px 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11.5px;
    font-weight: 700;
    color: #0f172a;
    white-space: nowrap;
  }
  .sandbox-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding-left: 20px;
    border-left: 1.5px dashed #94a3b8;
    text-align: center;
    flex: 1;
  }

  /* Priority Engine P1-P4 Grayscale Stepped Bar */
  .priority-bar {
    display: flex;
    width: 100%;
    height: 26px;
    border-radius: 4px;
    overflow: hidden;
    margin: 8px 0;
    border: 1.5px solid #1e293b;
  }
  .p-segment {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 800;
  }
  .p1 { background: #0f172a; color: #ffffff; }
  .p2 { background: #334155; color: #ffffff; }
  .p3 { background: #64748b; color: #ffffff; }
  .p4 { background: #cbd5e1; color: #0f172a; }

  /* Dashboard Tabs */
  .tabs-row {
    display: flex;
    gap: 4px;
    background: #f1f5f9;
    border: 1px solid #94a3b8;
    border-radius: 4px;
    padding: 2px;
    margin-top: 4px;
    justify-content: center;
  }
  .tab-btn {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 700;
    color: #334155;
  }
  .tab-btn.active {
    background: #1e293b;
    color: #ffffff;
    border-color: #1e293b;
  }

  /* Action Buttons */
  .action-btn {
    padding: 5px 14px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 800;
    background: #f8fafc;
    border: 1.5px solid #334155;
    color: #0f172a;
  }

  /* Threat grid */
  .threat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 4px;
  }

  /* Legend items */
  .legend-item {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
    font-weight: 600;
    color: #334155;
    margin-bottom: 9px;
  }
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <h1>CyberYukti: Autonomous Vulnerability Triage & Evidence Engine</h1>
  <h2>PS16 – System Architecture & Deterministic Dataflow</h2>
</div>

<!-- =========================================================================
     CARD 1: Input Scanners (Untrusted Boundary)
     ========================================================================= -->
<div class="untrusted-boundary">
  <div class="untrusted-tag top">[ Untrusted Input Boundary ]</div>
  <div class="untrusted-tag bottom">[ Untrusted Input Boundary ]</div>
  <div style="position:absolute; bottom:6px; right:8px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
    </svg>
  </div>
</div>

<div class="diag-box" style="left: 88px; top: 98px; width: 320px; height: 226px;">
  <div class="diag-title">Input Scanners</div>
  <div class="diag-subtitle">Multi-format security scanner reports</div>
  <div class="scanner-grid">
    <!-- Trivy -->
    <div class="scanner-item">
      <svg width="24" height="26" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin:0 auto 4px; display:block;">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
      </svg>
      <div class="scanner-name">Trivy</div>
      <div class="scanner-type">(SCA)</div>
    </div>
    <!-- Semgrep -->
    <div class="scanner-item">
      <svg width="24" height="26" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin:0 auto 4px; display:block;">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
      </svg>
      <div class="scanner-name">Semgrep</div>
      <div class="scanner-type">(SAST)</div>
    </div>
    <!-- Nuclei -->
    <div class="scanner-item">
      <svg width="24" height="26" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin:0 auto 4px; display:block;">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
      </svg>
      <div class="scanner-name">Nuclei</div>
      <div class="scanner-type">(DAST)</div>
    </div>
  </div>
  <div style="font-size:11px; color:#475569; text-align:center; margin-top:14px; font-weight:600;">
    Standardized Payloads: JSON · SARIF · YAML · CSV
  </div>
</div>

<!-- =========================================================================
     CARD 2: Ingestion & Normalization
     ========================================================================= -->
<div class="diag-box" style="left: 455px; top: 98px; width: 400px; height: 226px;">
  <div class="diag-title">Ingestion & Normalization</div>
  <div class="diag-subtitle">Normalizes multi-vendor syntax into unified models</div>
  <div style="display:flex; justify-content:space-between; align-items:center; height:100%; padding:0 6px;">
    <!-- Parsers Column -->
    <div class="parser-col">
      <div class="diag-node">Trivy JSON Parser</div>
      <div class="diag-node">Semgrep SARIF Parser</div>
      <div class="diag-node">Nuclei DAST Parser</div>
    </div>
    
    <!-- Arrows between parsers and canonical -->
    <svg width="45" height="120" viewBox="0 0 45 120" style="overflow:visible;">
      <path d="M 0 18 Q 22 18 40 50" fill="none" stroke="#1e293b" stroke-width="1.8" marker-end="url(#arr-dark)"/>
      <path d="M 0 60 L 40 60" fill="none" stroke="#1e293b" stroke-width="1.8" marker-end="url(#arr-dark)"/>
      <path d="M 0 102 Q 22 102 40 70" fill="none" stroke="#1e293b" stroke-width="1.8" marker-end="url(#arr-dark)"/>
    </svg>

    <!-- Canonical Schema Box -->
    <div class="canonical-cylinder">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:4px;">
        <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
      </svg>
      <div class="canonical-text">Canonical<br>Schema</div>
      <div style="font-size:9.5px; color:#475569; margin-top:3px; font-weight:700; font-family:monospace;">CanonicalFinding</div>
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 3: Deduplication Engine
     ========================================================================= -->
<div class="diag-box" style="left: 915px; top: 98px; width: 410px; height: 226px;">
  <div class="diag-title">Deduplication Engine</div>
  <div class="diag-subtitle">3-Stage Deterministic Clustering Engine</div>
  <div style="display:flex; flex-direction:column; gap:7px; margin-top:2px;">
    <div class="diag-node">1. Exact Hash Matching (SHA-256 Fingerprint)</div>
    <div class="diag-node">2. Semantic CWE Equivalence Clustering</div>
    <div class="diag-node">3. Cross-Tool SAST × DAST Correlation</div>
    <div style="background:#f8fafc; border:1.5px dashed #1e293b; border-radius:4px; padding:6px 10px; font-size:11.5px; font-weight:800; color:#0f172a; text-align:center; margin-top:2px;">
      90.5% Alert Noise Reduction (42 Alerts ➔ 4 Clusters)
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 4: Threat Intelligence
     ========================================================================= -->
<div class="diag-box" style="left: 1380px; top: 98px; width: 420px; height: 226px;">
  <div class="diag-title">Threat Intelligence</div>
  <div class="diag-subtitle">Real-time vulnerability feeds & exploitability feeds</div>
  <div class="threat-grid">
    <div class="diag-node" style="display:flex; align-items:center; justify-content:center; gap:6px;">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>
      NVD (CVSS v3.1)
    </div>
    <div class="diag-node" style="display:flex; align-items:center; justify-content:center; gap:6px;">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>
      EPSS (Probability)
    </div>
    <div class="diag-node" style="display:flex; align-items:center; justify-content:center; gap:6px;">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>
      CISA KEV (Exploited)
    </div>
    <div class="diag-node" style="display:flex; align-items:center; justify-content:center; gap:6px;">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>
      OSV Database
    </div>
  </div>
  <div style="font-size:11px; color:#475569; text-align:center; margin-top:14px; font-weight:600; line-height:1.4;">
    Enriches incident clusters with known weaponization & active wild exploitation
  </div>
</div>

<!-- =========================================================================
     CARD 5: Evidence Validation
     ========================================================================= -->
<div class="diag-box" style="left: 455px; top: 380px; width: 870px; height: 240px;">
  <div class="diag-title">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 12.5a6.002 6.002 0 0 1-5.83 5.996C13.5 18.5 12 17 8 17c-2.5 0-4 1-5 2-.5-1.5-.5-3.5 1-5 .5-.5 1-1 1-2 0-3 2.5-5 5.5-5 .5 0 1 .1 1.5.2A6 6 0 0 1 22 12.5z"></path>
      <rect x="2" y="10" width="3" height="3"></rect>
      <rect x="6" y="10" width="3" height="3"></rect>
      <rect x="10" y="10" width="3" height="3"></rect>
      <rect x="6" y="6" width="3" height="3"></rect>
      <rect x="10" y="6" width="3" height="3"></rect>
      <rect x="14" y="6" width="3" height="3"></rect>
    </svg>
    Evidence Validation (Deterministic Sandbox Prover)
  </div>
  <div class="diag-subtitle">
    Non-destructive, live environment reachability & presence validation
  </div>

  <div style="display:flex; height:100%; align-items:center; justify-content:space-between; margin-top:2px;">
    <!-- 4 Probes neatly grouped in 2x2 grid -->
    <div style="display:flex; flex-direction:column; gap:8px;">
      <div style="font-size:11.5px; font-weight:800; color:#0f172a; text-transform:uppercase; letter-spacing:0.5px;">
        Deterministic Safe Probes (All 4 Verified)
      </div>
      <div class="probes-grid">
        <div class="probe-pill">
          [PKG] Package Check <span style="font-size:10.5px; color:#475569; font-weight:700;">(Semver)</span>
        </div>
        <div class="probe-pill">
          [FILE] File Check <span style="font-size:10.5px; color:#475569; font-weight:700;">(Presence)</span>
        </div>
        <div class="probe-pill">
          [HTTP] Endpoint Check <span style="font-size:10.5px; color:#475569; font-weight:700;">(HTTP 200)</span>
        </div>
        <div class="probe-pill">
          [PORT] Port Check <span style="font-size:10.5px; color:#475569; font-weight:700;">(TCP Socket)</span>
        </div>
      </div>
      <div style="font-size:11px; color:#334155; font-weight:700; margin-top:2px;">
        Strict Allowlist Targets: <span style="font-family:monospace; color:#0f172a;">shop-api-01</span> · <span style="font-family:monospace; color:#0f172a;">shop-api-01-patched</span> · <span style="font-family:monospace; color:#0f172a;">db-cluster-01</span>
      </div>
    </div>

    <!-- Sandbox Isolation Info -->
    <div class="sandbox-info">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:4px;">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
      </svg>
      <div style="font-size:13px; font-weight:800; color:#0f172a;">
        Isolated | Non-root | 5.0s Timeout
      </div>
      <div style="font-size:11px; color:#475569; margin-top:2px; font-weight:600;">
        Zero Destructive Actions · Bounded Probes
      </div>
      <!-- Prover States Badge (Clean Grayscale/Plain Style) -->
      <div style="display:flex; gap:6px; margin-top:10px;">
        <span style="background:#f1f5f9; color:#0f172a; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1.5px solid #0f172a;">CONFIRMED</span>
        <span style="background:#f8fafc; color:#334155; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1.5px dashed #475569;">NOT_CONFIRMED</span>
        <span style="background:#ffffff; color:#64748b; font-size:10px; font-weight:800; padding:3px 8px; border-radius:4px; border:1px dotted #94a3b8;">INCONCLUSIVE</span>
      </div>
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 6: Priority Engine
     ========================================================================= -->
<div class="diag-box" style="left: 1380px; top: 380px; width: 420px; height: 240px;">
  <div class="diag-title">Priority Engine</div>
  <div class="diag-subtitle">P1–P4 Dynamic Risk Scoring Formula</div>
  
  <div class="priority-bar">
    <div class="p-segment p1">P1 (Critical)</div>
    <div class="p-segment p2">P2 (High)</div>
    <div class="p-segment p3">P3 (Medium)</div>
    <div class="p-segment p4">P4 (Low)</div>
  </div>

  <div style="font-size:11px; font-weight:700; color:#0f172a; text-align:center; margin-top:4px; font-family:monospace;">
    Score = 0.40·Severity + 0.25·Asset + 0.20·Exploit + 0.15·Validation
  </div>

  <div style="background:#f8fafc; border:1px solid #94a3b8; border-radius:4px; padding:8px 10px; margin-top:12px; text-align:center;">
    <div style="font-size:11.5px; font-weight:800; color:#0f172a;">
      Dynamic Re-Prioritization in Action
    </div>
    <div style="font-size:10.5px; color:#334155; font-weight:700; margin-top:2px;">
      Patched Asset Auto-Demoted: P2 ➔ P3 (Score: 62.0 ➔ 49.1)
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 7: AI Explanation Engine
     ========================================================================= -->
<div class="diag-box" style="left: 88px; top: 670px; width: 310px; height: 245px;">
  <div class="diag-title">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-2.04z"></path>
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-2.04z"></path>
    </svg>
    AI Explanation Engine
  </div>
  <div class="diag-subtitle">Dual-Rail Guarded Pipeline</div>

  <div style="display:flex; flex-direction:column; gap:7px; margin-top:4px;">
    <div class="diag-node">Input Sanitizer (24-Field Quarantine)</div>
    <div class="diag-node">Output Validator (Grounding & Schema)</div>
    <div style="background:#f8fafc; border:1px solid #64748b; border-radius:4px; padding:7px; text-align:center; font-size:10.5px; font-weight:800; color:#0f172a; margin-top:2px;">
      Zero-Trust: LLM never decides security truth or priority scores
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 8: Case Assembly & Dashboard
     ========================================================================= -->
<div class="diag-box" style="left: 470px; top: 670px; width: 855px; height: 145px;">
  <div class="diag-title">Case Assembly & Analyst Dashboard</div>
  <div class="diag-subtitle">Synthesizes evidence, scores, and explanations into an actionable queue</div>
  <div style="display:flex; justify-content:space-around; align-items:center; height:100%; margin-top:2px;">
    <!-- Sub-box 1 -->
    <div class="diag-node" style="width:245px; padding:10px 12px;">
      <div style="font-size:12px; font-weight:800; color:#0f172a;">Triage Case Assembly</div>
      <div style="font-size:10.5px; color:#475569; margin-top:3px; font-weight:600;">Evidence + Score + Root Cause</div>
    </div>
    <!-- Sub-box 2 -->
    <div class="diag-node" style="width:245px; padding:10px 12px;">
      <div style="font-size:12px; font-weight:800; color:#0f172a;">Analyst Dashboard</div>
      <div style="font-size:10.5px; color:#475569; margin-top:3px; font-weight:600;">Incident Queue & Live Probes</div>
    </div>
    <!-- Sub-box 3 -->
    <div class="diag-node" style="width:265px; padding:8px 10px;">
      <div style="font-size:11.5px; font-weight:800; color:#0f172a;">Interactive Analyst Views</div>
      <div class="tabs-row">
        <div class="tab-btn active">Stats</div>
        <div class="tab-btn">Cases</div>
        <div class="tab-btn">Detail</div>
      </div>
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 9: Human Approval
     ========================================================================= -->
<div class="diag-box" style="left: 470px; top: 840px; width: 570px; height: 85px;">
  <div style="display:flex; align-items:center; justify-content:space-between; height:100%; padding:0 10px;">
    <!-- Analyst Icon & Title -->
    <div style="display:flex; align-items:center; gap:10px;">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
      </svg>
      <div>
        <div style="font-size:13.5px; font-weight:800; color:#0f172a;">Human Approval</div>
        <div style="font-size:10.5px; color:#475569; font-weight:600;">Human-in-the-Loop Governance</div>
      </div>
    </div>
    <!-- Buttons -->
    <div style="display:flex; gap:8px;">
      <button class="action-btn">✓ Approve</button>
      <button class="action-btn">✕ Reject</button>
      <button class="action-btn">✎ Override</button>
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 10: Audit Trail
     ========================================================================= -->
<div class="diag-box" style="left: 470px; top: 950px; width: 570px; height: 85px;">
  <div style="display:flex; align-items:center; gap:12px; height:100%; padding:0 10px;">
    <!-- Database Icon -->
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
    </svg>
    <div>
      <div style="font-size:13.5px; font-weight:800; color:#0f172a;">Audit Trail</div>
      <div style="font-size:11px; color:#0f172a; font-weight:700;">
        Immutable Event Log with SHA-256 Hash Chain (<span style="font-family:monospace; font-weight:bold;">prev_hash</span>)
      </div>
      <div style="font-size:10px; color:#475569; font-weight:600;">
        SOC 2 / ISO 27001 Cryptographic Proof-of-Triage Non-Repudiation
      </div>
    </div>
  </div>
</div>

<!-- =========================================================================
     CARD 11: Legend Box (Draw.io style)
     ========================================================================= -->
<div class="diag-box" style="left: 1380px; top: 670px; width: 420px; height: 365px; background:#ffffff; border-color:#64748b;">
  <div class="diag-title" style="margin-bottom:12px; font-size:15px;">Legend & Architecture Symbols</div>
  
  <div class="legend-item">
    <svg width="36" height="14" viewBox="0 0 36 14">
      <line x1="0" y1="7" x2="26" y2="7" stroke="#0f172a" stroke-width="2"/>
      <polygon points="26,3 35,7 26,11" fill="#0f172a"/>
    </svg>
    <span><strong>Data flow (arrow)</strong> – Primary deterministic pipeline</span>
  </div>

  <div class="legend-item">
    <svg width="36" height="14" viewBox="0 0 36 14">
      <line x1="0" y1="7" x2="26" y2="7" stroke="#64748b" stroke-width="1.8" stroke-dasharray="4,3"/>
      <polygon points="26,3 35,7 26,11" fill="#64748b"/>
    </svg>
    <span><strong>Feedback / override (dashed)</strong> – Analyst tuning loop</span>
  </div>

  <div class="legend-item">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
    </svg>
    <span><strong>Trust boundary</strong> – Untrusted scan report isolation</span>
  </div>

  <div class="legend-item">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2">
      <path d="M22 12.5a6.002 6.002 0 0 1-5.83 5.996C13.5 18.5 12 17 8 17c-2.5 0-4 1-5 2-.5-1.5-.5-3.5 1-5 .5-.5 1-1 1-2 0-3 2.5-5 5.5-5 .5 0 1 .1 1.5.2A6 6 0 0 1 22 12.5z"></path>
    </svg>
    <span><strong>Sandbox (Docker)</strong> – Bounded probe execution</span>
  </div>

  <div class="legend-item">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2">
      <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
    </svg>
    <span><strong>External service</strong> – Threat intel feeds (NVD, KEV)</span>
  </div>

  <div class="legend-item">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1e293b" stroke-width="2">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    </svg>
    <span><strong>Deterministic Guardrail</strong> – Bounded validation rules</span>
  </div>

  <div style="border-top:1px solid #cbd5e1; padding-top:10px; margin-top:8px; font-size:11px; color:#475569; line-height:1.5;">
    <strong>PS16 Alignment:</strong> All 4 safe probes verified, mathematical scoring engine, zero hallucinated CVE authority, SHA-256 tamper-evident ledger.
  </div>
</div>

<!-- =========================================================================
     SVG CONNECTING ARROWS & DRAW.IO STYLE BADGE LABELS
     ========================================================================= -->
<svg class="connectors">
  <defs>
    <!-- Arrow marker dark slate -->
    <marker id="arr-dark" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0f172a"/>
    </marker>
    <!-- Arrow marker gray -->
    <marker id="arr-gray" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b"/>
    </marker>
  </defs>

  <!-- 1. Scanners to Ingestion: Raw Findings -->
  <path d="M 408 211 L 450 211" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="404" y="193" width="50" height="36" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="429" y="207" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Raw</text>
  <text x="429" y="221" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Findings</text>

  <!-- 2. Ingestion to Deduplication: Canonical Findings -->
  <path d="M 855 211 L 910 211" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="857" y="193" width="54" height="36" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="884" y="207" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Canonical</text>
  <text x="884" y="221" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Findings</text>

  <!-- 3. Deduplication <-> Threat Intelligence: Bi-directional Enrich -->
  <path d="M 1325 186 L 1375 186" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <path d="M 1380 231 L 1330 231" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="1331" y="167" width="44" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="1353" y="180" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Enrich</text>
  <rect x="1327" y="235" width="52" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="1353" y="248" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Enriched</text>

  <!-- 4. Deduplication to Evidence Validation: Incident Clusters -->
  <path d="M 1110 324 L 1110 375" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="1065" y="342" width="90" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="1110" y="355" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Incident Clusters</text>

  <!-- 5. Threat Intelligence to Priority Engine: Enriched Threat Data -->
  <path d="M 1590 324 L 1590 375" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="1530" y="342" width="120" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="1590" y="355" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Enriched Threat Data</text>

  <!-- 6. Evidence Validation to Priority Engine: Validated Clusters -->
  <path d="M 1325 500 L 1375 500" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="1328" y="482" width="48" height="36" rx="4" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="1352" y="496" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Validated</text>
  <text x="1352" y="510" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Clusters</text>

  <!-- 7. Priority Engine to Case Assembly: Priority Scores -->
  <path d="M 1450 620 L 1450 650 L 1200 650 L 1200 665" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="1275" y="641" width="88" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="1319" y="654" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Priority Scores</text>

  <!-- 8. AI Engine Inputs & Output -->
  <path d="M 25 725 L 82 725" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="18" y="716" width="66" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="51" y="729" font-size="9.5" font-weight="800" fill="#0f172a" text-anchor="middle">Verified Data</text>

  <path d="M 25 800 L 82 800" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="18" y="791" width="66" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="51" y="804" font-size="9.5" font-weight="800" fill="#0f172a" text-anchor="middle">Untrusted Text</text>

  <!-- Output from AI engine to Case Assembly -->
  <path d="M 398 742 L 465 742" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="403" y="733" width="58" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="432" y="746" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">AI Analysis</text>

  <!-- 9. Case Assembly to Human Approval -->
  <path d="M 740 815 L 740 835" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>

  <!-- 10. Human Approval to Audit Trail: Approved Cases -->
  <path d="M 740 925 L 740 945" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="696" y="926" width="88" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="740" y="939" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">Approved Cases</text>

  <!-- 11. AI Engine to Audit Trail (Audit log of AI explanations) -->
  <path d="M 243 915 L 243 992 L 465 992" fill="none" stroke="#0f172a" stroke-width="1.8" marker-end="url(#arr-dark)"/>
  <rect x="290" y="983" width="130" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="355" y="996" font-size="9.5" font-weight="700" fill="#0f172a" text-anchor="middle">AI Reasoning Audit Log</text>

  <!-- 12. Human Approval Feedback Loop to Case Assembly (Override / Reject) -->
  <path d="M 1040 882 L 1160 882 L 1160 820" fill="none" stroke="#64748b" stroke-width="1.8" stroke-dasharray="4,3" marker-end="url(#arr-gray)"/>
  <rect x="1058" y="873" width="88" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="1102" y="886" font-size="10" font-weight="800" fill="#64748b" text-anchor="middle">Override / Reject</text>

  <!-- 13. Analyst Feedback loop back to Untrusted Input Boundary -->
  <path d="M 470 535 L 247 535 L 247 345" fill="none" stroke="#64748b" stroke-width="1.8" stroke-dasharray="4,3" marker-end="url(#arr-gray)"/>
  <rect x="280" y="526" width="150" height="18" rx="3" fill="#ffffff" stroke="#64748b" stroke-width="1"/>
  <text x="355" y="539" font-size="10" font-weight="800" fill="#64748b" text-anchor="middle">Analyst Feedback & Tuning</text>

</svg>

</body>
</html>
"""

def generate_diagram():
    html_file = os.path.abspath("cyberyukti_architecture.html")
    png_file = os.path.abspath("cyberyukti_system_architecture.png")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"Wrote HTML to {html_file}")

    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    cmd = [
        edge_path,
        "--headless=new",
        "--disable-gpu",
        "--force-device-scale-factor=1.5",
        f"--screenshot={png_file}",
        "--window-size=1920,1080",
        f"file:///{html_file.replace(os.sep, '/')}"
    ]

    print("Rendering plain diagram with headless Edge...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Edge returncode:", res.returncode)
    if os.path.exists(png_file):
        print(f"Successfully generated {png_file} (Size: {os.path.getsize(png_file)} bytes)")
    else:
        print("Failed to generate PNG screenshot.")

if __name__ == "__main__":
    generate_diagram()
