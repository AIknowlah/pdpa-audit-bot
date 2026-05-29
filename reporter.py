"""
reporter.py
-----------
Generates two output artifacts from the PDPA compliance analysis result:
  1. A structured JSON report file
  2. A human-readable TXT summary report

Both files are written to the 'reports/' directory by default.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Severity display order and labels
SEVERITY_ORDER = ["High", "Medium", "Low"]

SEVERITY_ICONS = {
    "High":   "🔴",
    "Medium": "🟡",
    "Low":    "🟢",
}

STATUS_ICONS = {
    "Non-Compliant":       "✗",
    "Partially Compliant": "△",
    "Compliant":           "✓",
    "Not Assessed":        "—",
}


def generate_reports(
    analysis_result: dict[str, Any],
    source_file: str,
    output_dir: str = "reports",
) -> tuple[str, str]:
    """
    Write the JSON and TXT compliance reports and return their file paths.

    Args:
        analysis_result: Parsed dict returned by analyzer.analyse_document().
        source_file:     Path to the original document that was analysed.
        output_dir:      Directory where report files will be written.

    Returns:
        Tuple of (json_report_path, txt_report_path).
    """
    # Prepare output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Build a timestamped base name from the source file
    source_stem = Path(source_file).stem
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"{source_stem}_pdpa_report_{timestamp}"

    json_path = out_path / f"{base_name}.json"
    txt_path = out_path / f"{base_name}.txt"

    # Enrich the result with metadata before writing
    enriched = _enrich_result(analysis_result, source_file, timestamp)

    _write_json_report(enriched, json_path)
    _write_txt_report(enriched, txt_path)

    logger.info("JSON report written: %s", json_path)
    logger.info("TXT report written:  %s", txt_path)

    return str(json_path), str(txt_path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _enrich_result(
    result: dict[str, Any],
    source_file: str,
    timestamp: str,
) -> dict[str, Any]:
    """Add metadata fields to the analysis result dict."""
    disclaimer = (
        "This report is AI-generated using Google Gemini and is grounded in the "
        "PDPC Advisory Guidelines on Key Concepts in the PDPA (Revised 16 May 2022) "
        "and real PDPC enforcement decisions. It does not constitute legal advice. "
        "Findings should be verified by a qualified data protection professional or "
        "legal counsel before any compliance action is taken. For the latest "
        "regulatory guidance, refer to https://www.pdpc.gov.sg"
    )
    enriched = dict(result)
    enriched["metadata"] = {
        "source_file": os.path.basename(source_file),
        "source_file_full_path": str(Path(source_file).resolve()),
        "analysis_timestamp_utc": timestamp,
        "regulation": "Singapore Personal Data Protection Act (PDPA) 2012 (as amended)",
        "tool": "PDPA Audit Bot",
        "model": "gemini-2.5-flash",
        "disclaimer": disclaimer,
    }
    return enriched


def _write_json_report(result: dict[str, Any], path: Path) -> None:
    """Serialise the full result dict to a pretty-printed JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)


def _write_txt_report(result: dict[str, Any], path: Path) -> None:
    """Write a human-readable compliance report as plain text."""
    lines: list[str] = []
    meta = result.get("metadata", {})
    total = result.get("total_issues", {})
    obligations = result.get("obligations", [])

    def sep(char: str = "=", width: int = 80) -> str:
        return char * width

    def section(title: str) -> None:
        lines.append("")
        lines.append(sep())
        lines.append(f"  {title}")
        lines.append(sep())

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append(sep("="))
    lines.append("  PDPA COMPLIANCE AUDIT REPORT")
    lines.append("  Singapore Personal Data Protection Act 2012 (as amended)")
    lines.append(sep("="))
    lines.append(f"  Source File : {meta.get('source_file', 'N/A')}")
    lines.append(f"  Analysed On : {meta.get('analysis_timestamp_utc', 'N/A')} UTC")
    lines.append(f"  Model Used  : {meta.get('model', 'N/A')}")
    lines.append(sep("="))

    # ── Executive Summary ────────────────────────────────────────────────────
    section("EXECUTIVE SUMMARY")
    lines.append("")
    lines.append(f"  Document Type    : {result.get('document_summary', 'N/A')}")
    lines.append("")

    risk_level = result.get("overall_risk_level", "Unknown")
    risk_icon = SEVERITY_ICONS.get(risk_level, "❓")
    lines.append(f"  Overall Risk     : {risk_icon} {risk_level}")
    lines.append(f"  Justification    : {result.get('overall_risk_justification', 'N/A')}")
    lines.append("")
    lines.append("  Issue Count by Severity:")
    lines.append(f"    🔴 High   : {total.get('high', 0)}")
    lines.append(f"    🟡 Medium : {total.get('medium', 0)}")
    lines.append(f"    🟢 Low    : {total.get('low', 0)}")
    lines.append("    ──────────────────────────")
    total_count = total.get('high', 0) + total.get('medium', 0) + total.get('low', 0)
    lines.append(f"    Total     : {total_count}")

    # ── Key Recommendations ───────────────────────────────────────────────────
    section("KEY RECOMMENDATIONS (Priority Actions)")
    lines.append("")
    key_recs = result.get("key_recommendations", [])
    if not key_recs:
        lines.append("  No High-severity issues identified — no priority actions required.")
    else:
        urgency_icons = {
            "Immediate":   "🔴",
            "Short-term":  "🟡",
            "Medium-term": "🟢",
        }
        priority_labels = {
            1: "PRIORITY 1 — Immediate Legal Violation",
            2: "PRIORITY 2 — Critical Security Risk",
            3: "PRIORITY 3 — Financial / Contractual Exposure",
        }
        current_rank = None
        for i, rec in enumerate(key_recs, start=1):
            rank    = rec.get("priority_rank", 3)
            ob_name = rec.get("obligation_name", "Unknown")
            action  = rec.get("action_required", "N/A")
            urgency = rec.get("urgency", "Medium-term")
            icon    = urgency_icons.get(urgency, "❓")

            # Print a tier heading when the priority rank changes
            if rank != current_rank:
                current_rank = rank
                if i > 1:
                    lines.append("")
                lines.append(f"  ┌ {'─'*74}┐")
                lines.append(f"  │  {priority_labels.get(rank, f'PRIORITY {rank}'):<73}│")
                lines.append(f"  └ {'─'*74}┘")

            wrapped_action = _wrap_text(action, width=64, indent=" " * 17)
            lines.append(f"  [{i:02d}] {icon} [{urgency}]")
            lines.append(f"       Obligation  : {ob_name}")
            lines.append(f"       Action      : {wrapped_action}")
            lines.append("")

    # ── Compliance Status Overview ────────────────────────────────────────────
    section("COMPLIANCE STATUS OVERVIEW (All 11 Obligations)")
    lines.append("")
    lines.append(f"  {'#':<4} {'Obligation':<35} {'Status':<22} {'Issues'}")
    lines.append(f"  {'-'*4} {'-'*35} {'-'*22} {'-'*20}")
    for i, ob in enumerate(obligations, start=1):
        status = ob.get("status", "Unknown")
        icon = STATUS_ICONS.get(status, "?")
        issue_count = len(ob.get("issues", []))
        high_c = sum(1 for iss in ob.get("issues", []) if iss.get("severity") == "High")
        med_c  = sum(1 for iss in ob.get("issues", []) if iss.get("severity") == "Medium")
        low_c  = sum(1 for iss in ob.get("issues", []) if iss.get("severity") == "Low")
        issue_str = (
            f"H:{high_c} M:{med_c} L:{low_c}" if issue_count > 0 else "None"
        )
        lines.append(
            f"  {i:<4} {ob.get('obligation_name', 'Unknown'):<35} "
            f"{icon} {status:<20} {issue_str}"
        )

    # ── Detailed Findings ─────────────────────────────────────────────────────
    section("DETAILED FINDINGS BY OBLIGATION")

    for i, ob in enumerate(obligations, start=1):
        ob_name = ob.get("obligation_name", "Unknown")
        status  = ob.get("status", "Unknown")
        icon    = STATUS_ICONS.get(status, "?")
        issues  = ob.get("issues", [])

        lines.append("")
        lines.append(f"  [{i:02d}] {ob_name}")
        lines.append(f"       Status  : {icon} {status}")
        lines.append(f"       Summary : {ob.get('summary', 'N/A')}")

        if not issues:
            lines.append("       Issues  : None identified.")
        else:
            lines.append(f"       Issues  : {len(issues)} issue(s) found")
            for j, issue in enumerate(issues, start=1):
                sev = issue.get("severity", "Unknown")
                sev_icon = SEVERITY_ICONS.get(sev, "❓")
                lines.append("")
                lines.append(f"       Issue {j} {sev_icon} [{sev}]")
                lines.append(f"         Description : {issue.get('description', 'N/A')}")
                doc_ref = issue.get("document_reference", "N/A")
                # Wrap long document references
                wrapped_ref = _wrap_text(doc_ref, width=65, indent=" " * 23)
                lines.append(f"         Document Ref: {wrapped_ref}")
                rec = issue.get("recommendation", "N/A")
                wrapped_rec = _wrap_text(rec, width=65, indent=" " * 23)
                lines.append(f"         Remediation : {wrapped_rec}")

        # ── Relevant PDPC Precedents ──────────────────────────────────────
        precedents = ob.get("precedent_cases", [])
        if precedents:
            lines.append("")
            lines.append("       RELEVANT PRECEDENTS (PDPC Enforcement Cases)")
            lines.append(f"       {'·' * 55}")
            for k, case in enumerate(precedents, start=1):
                case_name = case.get("case_name", "Unknown")
                citation  = case.get("citation", "N/A")
                penalty   = case.get("penalty_imposed", "N/A")
                breach    = case.get("breach_type", "")
                summary   = case.get("summary", "")

                lines.append(f"       Case {k}: {case_name}")
                lines.append(f"         Citation : {citation}")
                lines.append(f"         Penalty  : {penalty}")
                if breach:
                    wrapped_breach = _wrap_text(breach, width=60, indent=" " * 21)
                    lines.append(f"         Breach   : {wrapped_breach}")
                if summary:
                    wrapped_summary = _wrap_text(summary, width=60, indent=" " * 21)
                    lines.append(f"         Summary  : {wrapped_summary}")
                if k < len(precedents):
                    lines.append("")

        lines.append(f"  {'-'*76}")


    # ── Footer ────────────────────────────────────────────────────────────────
    lines.append("")
    lines.append(sep("="))
    lines.append("  DISCLAIMER")
    lines.append(sep("-"))
    disclaimer_text = (
        "  This report is AI-generated using Google Gemini and is grounded in the\n"
        "  PDPC Advisory Guidelines on Key Concepts in the PDPA (Revised 16 May 2022)\n"
        "  and real PDPC enforcement decisions. It does not constitute legal advice.\n"
        "  Findings should be verified by a qualified data protection professional or\n"
        "  legal counsel before any compliance action is taken. For the latest\n"
        "  regulatory guidance, refer to https://www.pdpc.gov.sg\n\n"
        "  Case precedents cited in this report are sourced from publicly\n"
        "  available PDPC enforcement decisions at pdpc.gov.sg"
    )
    lines.append(disclaimer_text)
    lines.append(sep("="))
    lines.append("")

    # Write file
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def _wrap_text(text: str, width: int = 70, indent: str = "") -> str:
    """
    Simple word-wrap helper. First line is returned as-is (caller already
    indents it); subsequent lines are prefixed with `indent`.
    """
    if not text or len(text) <= width:
        return text

    words = text.split()
    result_lines: list[str] = []
    current_line: list[str] = []
    current_len = 0

    for word in words:
        if current_len + len(word) + (1 if current_line else 0) > width:
            if current_line:
                result_lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)
            else:
                result_lines.append(word)
                current_len = 0
        else:
            current_line.append(word)
            current_len += len(word) + (1 if len(current_line) > 1 else 0)

    if current_line:
        result_lines.append(" ".join(current_line))

    return f"\n{indent}".join(result_lines)
