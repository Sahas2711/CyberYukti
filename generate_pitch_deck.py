"""Generates a professional 16:9 PowerPoint presentation for CyberYukti (PS16).

CyberYukti — Autonomous Vulnerability Triage & Evidence Engine
ACSC Hackathon Pitch Deck
"""

import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# Color Palette (Dark Theme / Cybersecurity Cyberpunk Professional)
# ---------------------------------------------------------------------------
BG_DARK = RGBColor(13, 17, 23)        # #0D1117 GitHub Dark / Night
CARD_BG = RGBColor(22, 27, 34)        # #161B22 Panel Charcoal
CARD_BORDER = RGBColor(48, 54, 61)    # #30363D Border faint
CYAN = RGBColor(0, 229, 255)          # #00E5FF Accent Cyan
EMERALD = RGBColor(16, 185, 129)      # #10B981 Success Confirmed
AMBER = RGBColor(245, 158, 11)        # #F59E0B Warning / Risk
CORAL = RGBColor(239, 68, 68)         # #EF4444 High Critical / Bug
TEXT_WHITE = RGBColor(240, 246, 252)  # #F0F6FC
TEXT_MUTED = RGBColor(139, 148, 158)  # #8B949E Muted secondary
TEXT_CYAN = RGBColor(56, 189, 248)    # #38BDF8 Light Cyan


def create_deck(output_filename="CyberYukti_PS16_Pitch_Deck.pptx"):
    prs = Presentation()
    # 16:9 Widescreen standard dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Blank layout

    def add_slide_base(category="PS16 EXPERT TRACK • ACSC HACKATHON", title="Slide Title"):
        slide = prs.slides.add_slide(blank_layout)
        # Background fill
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()

        # Header Category / Subtitle
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = CYAN

        # Header Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.8))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE

        return slide

    def add_card(slide, left, top, width, height, title="", text="", accent_color=None, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)

        tf = card.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.TOP
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.25)
        tf.margin_bottom = Inches(0.2)

        if title:
            p_title = tf.paragraphs[0]
            p_title.text = title
            p_title.font.size = Pt(15)
            p_title.font.bold = True
            p_title.font.color.rgb = accent_color or TEXT_WHITE
            p_title.space_after = Pt(8)

        if text:
            first = False if title else True
            for line in text.strip().split("\n"):
                if first:
                    p = tf.paragraphs[0]
                    first = False
                else:
                    p = tf.add_paragraph()
                p.text = line
                p.font.size = Pt(12)
                p.font.color.rgb = TEXT_MUTED
                p.space_after = Pt(4)

        return card

    # =========================================================================
    # SLIDE 1: Title Slide (Cover)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_DARK
    bg1.line.fill.background()

    # Title box
    tbox = slide1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.8))
    tf1 = tbox.text_frame
    tf1.word_wrap = True

    p_sub = tf1.paragraphs[0]
    p_sub.text = "ACSC HACKATHON — PS16 EXPERT TRACK"
    p_sub.font.size = Pt(14)
    p_sub.font.bold = True
    p_sub.font.color.rgb = CYAN
    p_sub.space_after = Pt(14)

    p_main = tf1.add_paragraph()
    p_main.text = "CyberYukti"
    p_main.font.size = Pt(54)
    p_main.font.bold = True
    p_main.font.color.rgb = TEXT_WHITE
    p_main.space_after = Pt(10)

    p_desc = tf1.add_paragraph()
    p_desc.text = "Autonomous Vulnerability Triage & Deterministic Evidence Engine"
    p_desc.font.size = Pt(22)
    p_desc.font.color.rgb = TEXT_CYAN
    p_desc.space_after = Pt(16)

    p_tag = tf1.add_paragraph()
    p_tag.text = "From Noisy Scanner Flood to Cryptographically Verified, Analyst-Ready Security Cases."
    p_tag.font.size = Pt(14)
    p_tag.font.color.rgb = TEXT_MUTED

    # Highlights banner on bottom
    banner = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(5.8), Inches(11.333), Inches(0.9))
    banner.fill.solid()
    banner.fill.fore_color.rgb = CARD_BG
    banner.line.color.rgb = CYAN
    banner.line.width = Pt(1)
    tf_b = banner.text_frame
    tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_b = tf_b.paragraphs[0]
    p_b.text = "⚡ 90.5% Alert Noise Reduction   |   🔬 Zero-LLM Deterministic Prover   |   🛡️ Poison-Proof AI Defense   |   📜 Cryptographic Audit Ledger"
    p_b.alignment = PP_ALIGN.CENTER
    p_b.font.size = Pt(13)
    p_b.font.bold = True
    p_b.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 2: The Problem (The Enterprise AppSec Crisis)
    # =========================================================================
    s2 = add_slide_base("01. THE PROBLEM STATEMENT", "The Modern SecOps Dilemma: Drowning in Scanner Noise")
    add_card(s2, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8),
             title="🚨 1. Alert Fatigue & Duplication",
             text="• Multiple scanners (Trivy, Semgrep, Nuclei) report the exact same bug with different names.\n• 1 real vulnerability generates 10+ alerts across CI/CD.\n• SOC analysts spend 80% of their day manually de-duplicating CSV reports.",
             accent_color=CORAL)
    add_card(s2, Inches(4.85), Inches(1.8), Inches(3.6), Inches(4.8),
             title="👻 2. Stale & Ghost Findings",
             text="• Scanners flag libraries without checking if the file is called or if the route is open.\n• Up to 40% of scanner alerts are already patched in production or completely unreachable.\n• Hours wasted investigating vulnerabilities that don't exist.",
             accent_color=AMBER)
    add_card(s2, Inches(8.9), Inches(1.8), Inches(3.6), Inches(4.8),
             title="⚠️ 3. The 'Naive AI' Trap",
             text="• Generic AI triage tools blindly ask ChatGPT: 'Is this vulnerable?'.\n• LLMs hallucinate CVEs, make up package versions, and fail.\n• Prompt Injection Danger: Attackers embed instructions in HTTP responses to hijack AI triage.",
             accent_color=CYAN)

    # =========================================================================
    # SLIDE 3: The Solution Overview (End-to-End Architecture)
    # =========================================================================
    s3 = add_slide_base("02. SOLUTION OVERVIEW", "CyberYukti Dual-Rail Autonomous Architecture")
    
    # 4 Flow Steps
    cards_data = [
        ("Step 1: Normalization & Dedup", "• Ingests Trivy, Semgrep, Nuclei, SARIF, CSV.\n• Stage 1: Exact Hash Dedup.\n• Stage 2: Generic CWE Exclusion.\n• Stage 3: SAST-to-DAST Route Correlation.\n• Result: 90.5% Noise Eliminated.", CYAN),
        ("Step 2: Evidence Validation", "• Controlled Lab Target Sandbox.\n• Zero-LLM Deterministic Probes.\n• Package version, HTTP endpoint, TCP port, & file existence checks.\n• Three-State: CONFIRMED, NOT_CONFIRMED, INCONCLUSIVE.", EMERALD),
        ("Step 3: Dynamic Risk Scoring", "• Formula: 40% Sev + 25% Asset + 20% Exposure + 15% Validation.\n• Deterministic P1 to P4 Priority.\n• Dynamic Shift: Confirmed bugs stay high; Patched bugs auto-demote to P3/P4.", AMBER),
        ("Step 4: AI & Human Approval", "• Sanitized Prompt Engine (24 fields).\n• Hallucination validator blocks fake CVEs.\n• Analyst Approve / Reject / Override.\n• SHA-256 Hash Chained Audit Ledger.", TEXT_CYAN),
    ]
    for idx, (ctitle, ctext, ccol) in enumerate(cards_data):
        add_card(s3, Inches(0.8 + idx * 2.95), Inches(1.8), Inches(2.75), Inches(4.8),
                 title=ctitle, text=ctext, accent_color=ccol)

    # =========================================================================
    # SLIDE 4: Person 1 Track — Ingestion & Deduplication
    # =========================================================================
    s4 = add_slide_base("03. PERSON 1 TRACK", "Finding Intelligence & 3-Tier Multi-Tool Correlation")
    add_card(s4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8),
             title="Triple-Tier Deduplication Engine",
             text="1. Exact Hash Fingerprinting:\n   • Hashes (Asset ID + Package / File Path + CVE / Rule ID).\n   • Drops duplicate scan alerts instantly with O(1) lookups.\n\n2. Generic CWE Exclusion:\n   • Suppresses vague scanner findings (CWE-20, CWE-398) when a specific CVE already identifies the vulnerability.\n\n3. SAST-to-DAST Route Correlation:\n   • Bridges code findings (Semgrep `static.py`) with live web traffic (Nuclei `/api/static/download`).\n   • Unifies disparate tool alerts into one cohesive Incident Cluster.",
             accent_color=CYAN)
    add_card(s4, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8),
             title="Verified Benchmark Results",
             text="📊 Enterprise Scan Benchmark (Trivy + Semgrep + Nuclei):\n\n• Raw Scanner Alerts Ingested: 42 findings\n• Deduplicated Incident Clusters: 4 clusters\n• Clutter & Noise Elimination: 90.48% Noise Reduction\n\n⚡ Multi-Format Enterprise Ingestion:\n• Supports Multipart File Upload (JSON, CSV, SARIF).\n• Remote Report URL fetching.\n• Enterprise Stress Benchmark: Tested with 10,000 findings processed in 1.1 seconds with zero dropped records.",
             accent_color=EMERALD)

    # =========================================================================
    # SLIDE 5: Person 2 Track — Safe Evidence Validation Engine
    # =========================================================================
    s5 = add_slide_base("04. PERSON 2 TRACK", "Evidence Validation Engine — Zero-LLM, Safe & Bounded")
    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8),
             title="Deterministic Read-Only Probes",
             text="• PACKAGE_VERSION Probe:\n  Inspects target packages manifest. Evaluates semver ranges using packaging.version (e.g. jQuery 1.12.4 vs 3.6.0).\n\n• HTTP_ENDPOINT Probe:\n  Safe GET/HEAD with strict timeout, follow_redirects=False, verifying actual server response codes.\n\n• PORT_CHECK Probe:\n  Safe TCP socket connect_ex check against target allowlist.\n\n• FILE_EXISTS Probe:\n  Path canonicalization with strict path jail (prevents ../ traversal).",
             accent_color=EMERALD)
    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8),
             title="Dual-Mode Sandbox & Strict Safety Rules",
             text="🛡️ ACSC Safety Guardrails Strictly Maintained:\n• Zero Autonomous Exploitation — we verify evidence, never attack or pop shells.\n• Strict Target Allowlist (`LAB_TARGETS`) — SSRF boundaries enforce only pre-approved hosts can be probed.\n\n🐳 Dual-Mode Execution Sandbox:\n• Docker Containment: --user=10001:10001 (non-root), --network=lab-net, --read-only, --cap-drop=ALL, --security-opt=no-new-privileges, 256MB RAM.\n• Subprocess Jail Fallback: Enforces shell=False, 5.0s timeout, and 10KB stdout/stderr truncation caps.",
             accent_color=CYAN)

    # =========================================================================
    # SLIDE 6: Person 3 Track — Dynamic Prioritization
    # =========================================================================
    s6 = add_slide_base("05. PERSON 3 TRACK", "Deterministic Risk Formula & Real-Time Re-Prioritization")
    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8),
             title="The Mathematical Scoring Formula",
             text="CyberYukti replaces arbitrary AI scores with a transparent mathematical formula:\n\nScore = (0.40 × Severity) + (0.25 × Asset Criticality)\n        + (0.20 × Exposure) + (0.15 × Validation)\n\nPriority Tiers:\n• P1 (Critical Immediate): Score ≥ 80.0\n• P2 (High Priority): Score 60.0 – 79.9\n• P3 (Medium Priority): Score 35.0 – 59.9\n• P4 (Low / Informational): Score < 35.0\n\nEvery scoring factor is transparently audited and displayed.",
             accent_color=AMBER)
    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8),
             title="Dynamic Validation Sensitivity (Live Demotion)",
             text="The defining differentiator of CyberYukti:\n\n🔴 TARGET A: VULNERABLE (`shop-api-01`)\n• Probe confirms jQuery 1.12.4 installed.\n• Status: CONFIRMED (Factor = 0.95)\n• Score: 62.0 ➔ Priority: P2 Retained.\n\n🟢 TARGET B: PATCHED (`shop-api-01-patched`)\n• Probe discovers jQuery 3.6.0 installed.\n• Status: NOT_CONFIRMED (Factor drops to 0.10)\n• Score drops from 62.0 ➔ 49.1!\n• Priority: Dynamically demoted from P2 down to P3!\n• Zero analyst hours wasted on fixed vulnerabilities.",
             accent_color=TEXT_WHITE)

    # =========================================================================
    # SLIDE 7: Person 4 Track — AI Safety & Analyst Workflow
    # =========================================================================
    s7 = add_slide_base("06. PERSON 4 TRACK", "Dual-Rail AI Defense & Human-in-the-Loop Workflow")
    add_card(s7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8),
             title="Adversarial Injection & Hallucination Defense",
             text="🛡️ 24-Field Prompt Sanitizer:\n• Quarantines raw scanner observations with <UNTRUSTED> delimiters.\n• Defends against DAN jailbreaks, instruction overrides, and shell dropping payloads.\n\n🔍 Strict Output Validator:\n• Enforces strict Pydantic JSON schema.\n• Grounding Verification: Checks that every CVE and CVSS score in the AI explanation exists in the original finding.\n• 16/16 Adversarial & Hallucination Tests 100% Passed.",
             accent_color=CORAL)
    add_card(s7, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8),
             title="Analyst Governance & Web UI",
             text="👩‍💻 Next.js 14 Responsive Security Dashboard:\n• Executive KPI Strip & Ingestion Noise Reduction Metrics.\n• Priority Queue & Multi-Factor Filterable Case Table.\n• Live Probe Trigger directly from the browser.\n\n⚖️ Human Approval Controls:\n• Approve: One-click confirmation.\n• Reject: Enforces mandatory justification reason.\n• Override: Allows priority adjustment (e.g. P2 ➔ P1) with full tracking of previous vs new priority.",
             accent_color=CYAN)

    # =========================================================================
    # SLIDE 8: Cryptographic Audit Trail
    # =========================================================================
    s8 = add_slide_base("07. COMPLIANCE & GOVERNANCE", "Cryptographic Proof-of-Triage: The Immutable Ledger")
    add_card(s8, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8),
             title="Tamper-Evident Hash Chaining",
             text="In enterprise environments (SOC 2, ISO 27001, PCI-DSS), auditability is mandatory.\n\nEvery action in CyberYukti is immutably recorded:\n1. Event Creation: Unique UUID + ISO UTC Timestamp.\n2. Actor Attribution: Identifies actor (system, analyst, or ai).\n3. State Mutation: Captures previous_state and new_state.\n4. Hash Chain: Every event embeds `prev_hash` pointing to the prior event ID.\n\nAny retroactive tampering breaks the cryptographic chain.",
             accent_color=TEXT_CYAN)
    add_card(s8, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8),
             title="Full Lifecycle Case Provenance",
             text="A complete historical record from scan to resolution:\n\n[08:00] Ingested: Nuclei, Semgrep, Trivy findings\n   │  Hash: evt-01 · prev_hash: null\n   ▼\n[08:30] Clustered: 3 alerts unified into CLUSTER-001\n   │  Hash: evt-02 · prev_hash: evt-01\n   ▼\n[08:35] Validated: PACKAGE_VERSION probe executed\n   │  Hash: evt-03 · prev_hash: evt-02\n   ▼\n[08:40] Prioritized: Formula executed (Score 92.5, P1)\n   │  Hash: evt-04 · prev_hash: evt-03\n   ▼\n[09:00] Analyst Action: Approved with remediation note",
             accent_color=EMERALD)

    # =========================================================================
    # SLIDE 9: Live Demo Scenarios (The 3 Judge Walkthroughs)
    # =========================================================================
    s9 = add_slide_base("08. LIVE DEMONSTRATION", "The 3 Core Hackathon Demo Scenarios")
    add_card(s9, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8),
             title="Scenario A: Confirmed Bug",
             text="🎯 Target: shop-api-01\n\n• Scanner claims outdated jQuery 1.12.4.\n• Analyst clicks '⚡ Run Live Probe'.\n• Probe inspects packages.json.\n• Finds: 1.12.4 (vulnerable).\n• Status: CONFIRMED (96% conf).\n• Score: 62.0 (Retains P2 Priority).\n• AI generates grounded remediation advice.\n• Analyst approves for immediate patching.",
             accent_color=CORAL)
    add_card(s9, Inches(4.85), Inches(1.8), Inches(3.6), Inches(4.8),
             title="Scenario B: Stale / Patched Bug",
             text="🎯 Target: shop-api-01-patched\n\n• Scanner flags old build artifact.\n• Analyst selects patched target.\n• Probe inspects live packages.json.\n• Finds: 3.6.0 (patched version).\n• Status: NOT_CONFIRMED!\n• Contradiction detected.\n• Dynamic Shift: Priority drops from P2 ➔ P3!\n• Zero engineer hours wasted on fixed bug.",
             accent_color=EMERALD)
    add_card(s9, Inches(8.9), Inches(1.8), Inches(3.6), Inches(4.8),
             title="Scenario C: Inconclusive Fail-Safe",
             text="🎯 Target: unregistered-asset\n\n• Scanner targets unknown host.\n• Target registry allowlist blocks SSRF.\n• Probe cannot connect.\n• Status: INCONCLUSIVE.\n• Golden Safety Rule: Execution failure NEVER converts to 'Not Confirmed'.\n• Flagged for manual analyst verification without false security assumptions.",
             accent_color=AMBER)

    # =========================================================================
    # SLIDE 10: Technical Verification & Metrics
    # =========================================================================
    s10 = add_slide_base("09. EMPIRICAL VALIDATION", "90 Automated Tests Passed Across All 4 Tracks")
    
    # 3 Stat Cards
    add_card(s10, Inches(0.8), Inches(1.8), Inches(3.6), Inches(2.2),
             title="77 Backend & Service Tests",
             text="• 14 Ingestion & Bridge Tests: PASSED\n• 43 Evidence Engine Tests: PASSED\n• 16 AI Safety & Injection Tests: PASSED\n• 4 Risk Engine Tests: PASSED",
             accent_color=CYAN)
    add_card(s10, Inches(4.85), Inches(1.8), Inches(3.6), Inches(2.2),
             title="13 Frontend Vitest Tests",
             text="• 8 Injection UI Render Tests: PASSED\n• 5 Live Probe & Status Tests: PASSED\n• 0 React or TypeScript Warnings",
             accent_color=EMERALD)
    add_card(s10, Inches(8.9), Inches(1.8), Inches(3.6), Inches(2.2),
             title="Next.js Production Build",
             text="• 100% Valid Typescript Compilation\n• Zero ESLint Violations\n• Optimized Static & Dynamic Bundles",
             accent_color=TEXT_CYAN)

    # Bottom summary card
    add_card(s10, Inches(0.8), Inches(4.3), Inches(11.7), Inches(2.3),
             title="Section 28 Benchmark Metrics (Evidence Engine Evaluation)",
             text="• Benchmark Test Cases: 10/10 Correct (100.0% Accuracy)\n• False Confirmations: 0  |  False Rejections: 0  |  Inconclusive Safety Fallbacks: 3\n• Adversarial Payload Injection Rejection: 6/6 (100% Neutralized)\n• Noise Reduction: 42 raw findings ➔ 4 clusters (90.48% Reduction)\n• 10,000 Finding Enterprise Benchmark: Successfully completed in 1.12 seconds.",
             accent_color=TEXT_WHITE)

    # =========================================================================
    # SLIDE 11: Competitive USPs & Conclusion
    # =========================================================================
    s11 = add_slide_base("10. COMPETITIVE EDGE", "Why CyberYukti Wins: 4 Killer USPs")
    add_card(s11, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.3),
             title="1. Dual-Rail Zero-Trust Architecture",
             text="We never let an LLM decide security truth. The prover is 100% deterministic code; the AI is bounded strictly to explanation with hallucination guardrails.",
             accent_color=CYAN)
    add_card(s11, Inches(6.8), Inches(1.8), Inches(5.7), Inches(2.3),
             title="2. Dynamic Real-Time Re-Prioritization",
             text="When an asset is patched, the score dynamically recalculates live, demoting priority from P2 to P3 instantly without page refreshes.",
             accent_color=EMERALD)
    add_card(s11, Inches(0.8), Inches(4.3), Inches(5.6), Inches(2.3),
             title="3. Cross-Tool Reachability Triangulation",
             text="Correlates SCA package alerts (Trivy), SAST code sinks (Semgrep), and DAST public web endpoints (Nuclei) into a unified attack chain.",
             accent_color=AMBER)
    add_card(s11, Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.3),
             title="4. Compliance-Ready Hash Ledger",
             text="Every probe execution, score change, and analyst override is recorded with prev_hash chaining for SOC 2 and ISO 27001 auditability.",
             accent_color=CORAL)

    # Save presentation
    prs.save(output_filename)
    print(f"[SUCCESS] Presentation generated successfully: {output_filename}")


if __name__ == "__main__":
    out_file = "CyberYukti_PS16_Pitch_Deck.pptx"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    create_deck(out_file)
