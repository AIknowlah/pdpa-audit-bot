"""
analyzer.py
-----------
Sends extracted document text to Google Gemini (gemini-2.5-flash) and
receives a structured PDPA compliance analysis covering all 11 obligations.

The analysis prompt is grounded with authoritative PDPC reference text
(from pdpa_reference.py) and enriched post-analysis with real PDPC
enforcement case precedents (from pdpa_cases.py).

The Gemini API key is read from the GEMINI_API_KEY environment variable,
which should be stored in a .env file and loaded before calling this module.
"""

import json
import logging
import os
import re
import textwrap
import time
from typing import Any

import vertexai
from vertexai.generative_models import GenerativeModel

from pdpa_reference import get_reference_prompt
from pdpa_cases import get_cases_for_obligation, format_cases_for_report

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PDPA Obligation definitions used in the prompt
# ---------------------------------------------------------------------------
PDPA_OBLIGATIONS: list[dict[str, str]] = [
    {
        "id": "purpose_limitation",
        "name": "Purpose Limitation",
        "description": (
            "Personal data must only be collected for purposes that a reasonable "
            "person would consider appropriate in the circumstances, and used/disclosed "
            "only for those purposes or directly related ones. Organisations must not "
            "collect data 'just in case' or for vague unstated purposes."
        ),
    },
    {
        "id": "notification",
        "name": "Notification",
        "description": (
            "Before collecting personal data, organisations must notify individuals "
            "of the purposes of collection and how to contact the organisation. "
            "This includes data collected through third parties."
        ),
    },
    {
        "id": "consent",
        "name": "Consent",
        "description": (
            "Organisations must obtain voluntary, informed consent before collecting, "
            "using, or disclosing personal data (unless an exception applies). "
            "Consent must not be made a condition of service unless it is necessary. "
            "Individuals must be able to withdraw consent and be informed of the "
            "consequences of doing so."
        ),
    },
    {
        "id": "access_and_correction",
        "name": "Access and Correction",
        "description": (
            "Individuals have the right to access their personal data held by an "
            "organisation and to correct inaccurate data. Organisations must respond "
            "to access requests within 30 calendar days (extendable to 60 with notice). "
            "A reasonable fee may be charged but it must not be excessive. "
            "Organisations cannot unreasonably refuse correction requests."
        ),
    },
    {
        "id": "accuracy",
        "name": "Accuracy",
        "description": (
            "Organisations must make reasonable effort to ensure that personal data "
            "collected is accurate and complete, especially when it is likely to be "
            "used to make a decision that affects the individual, or disclosed to "
            "another organisation."
        ),
    },
    {
        "id": "protection",
        "name": "Protection",
        "description": (
            "Organisations must protect personal data with reasonable security "
            "arrangements to prevent unauthorised access, collection, use, disclosure, "
            "copying, modification, disposal, or similar risks. This includes technical, "
            "administrative, and physical safeguards. Credentials and passwords must "
            "never be stored or shared insecurely."
        ),
    },
    {
        "id": "retention_limitation",
        "name": "Retention Limitation",
        "description": (
            "Personal data must not be retained longer than is necessary for legal "
            "or business purposes. Organisations must have clear data retention "
            "schedules and dispose of personal data securely when it is no longer needed."
        ),
    },
    {
        "id": "transfer_limitation",
        "name": "Transfer Limitation",
        "description": (
            "Personal data may only be transferred outside Singapore if the recipient "
            "country provides a standard of protection comparable to Singapore's PDPA, "
            "OR if the organisation ensures equivalent protection through contractual "
            "or other means (e.g., binding corporate rules, data transfer agreements). "
            "Organisations must assess recipient countries before transferring data."
        ),
    },
    {
        "id": "data_breach_notification",
        "name": "Data Breach Notification",
        "description": (
            "Organisations must notify the PDPC (Personal Data Protection Commission) "
            "within 3 calendar days of assessing that a notifiable data breach has "
            "occurred. Affected individuals must also be notified as soon as "
            "practicable. Organisations must have an incident response plan in place."
        ),
    },
    {
        "id": "accountability",
        "name": "Accountability",
        "description": (
            "Organisations must appoint a Data Protection Officer (DPO), develop "
            "and implement data protection policies and practices, conduct data "
            "protection impact assessments (DPIAs) for high-risk activities, and "
            "be able to demonstrate compliance. Staff must receive appropriate training."
        ),
    },
    {
        "id": "do_not_call",
        "name": "Do Not Call (DNC) Registry",
        "description": (
            "Before sending unsolicited telemarketing messages (voice calls, SMS, fax) "
            "to Singapore telephone numbers, organisations must check the DNC Registry "
            "and must not contact numbers registered on the DNC Registry unless clear "
            "and unambiguous consent has been obtained from the individual. "
            "This applies regardless of whether the organisation maintains its own "
            "internal do-not-call list."
        ),
    },
]


# ---------------------------------------------------------------------------
# Gemini client setup
# ---------------------------------------------------------------------------

def _get_gemini_client() -> GenerativeModel:
    """
    Initialise and return a Gemini GenerativeModel instance using Vertex AI.
    Reads config from env (GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_REGION, GEMINI_MODEL).
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    region = os.environ.get("GOOGLE_CLOUD_REGION", "asia-southeast1").strip()
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()

    if not project_id:
        raise EnvironmentError(
            "GOOGLE_CLOUD_PROJECT environment variable is not set. "
            "Please configure it in your .env file."
        )

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=region)

    model = GenerativeModel(
        model_name=model_name,
        generation_config={
            "temperature": 0.1,        # Low temperature for deterministic compliance analysis
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",  # Force JSON output
        },
    )
    logger.info(
        "Gemini client initialised via Vertex AI (Project: %s, Region: %s, Model: %s)",
        project_id, region, model_name
    )
    return model


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(document_text: str) -> str:
    """
    Build the structured prompt sent to Gemini for PDPA compliance analysis.
    The prompt is prefixed with authoritative PDPC reference text from
    pdpa_reference.py to ground the model's analysis in official guidance.
    """
    reference_block = get_reference_prompt()

    obligations_block = "\n".join(
        f"  {i+1}. [{ob['name']}] — {ob['description']}"
        for i, ob in enumerate(PDPA_OBLIGATIONS)
    )

    prompt = textwrap.dedent(f"""
    {reference_block}

    You are an expert Singapore PDPA (Personal Data Protection Act 2012, as amended)
    compliance auditor. Your task is to analyse the provided document and identify
    compliance issues against each of the 11 PDPA obligations.

    ## PDPA Obligations to Audit
    {obligations_block}

    ## Severity Levels
    - **High**: A clear and direct violation of the PDPA that creates significant 
      legal risk or harm to individuals. Regulatory action is likely.
    - **Medium**: A practice that is non-compliant or falls short of PDPA requirements, 
      posing moderate risk. Remediation is recommended.
    - **Low**: A gap or best-practice concern that, while not a direct breach, could 
      become non-compliant if left unaddressed.

    ## Your Task
    Analyse the document below for compliance with each of the 11 obligations. Be extremely concise in your descriptions and recommendations (one short sentence each) to prevent the JSON response from being truncated.

    ## Required Output Format
    Return a single valid JSON object matching this exact schema:

    {{
      "document_summary": "One sentence summary of the document type and purpose",
      "overall_risk_level": "High | Medium | Low",
      "overall_risk_justification": "One-sentence explanation of the overall risk rating",
      "obligations": [
        {{
          "obligation_id": "<id from the list above>",
          "obligation_name": "<obligation name>",
          "status": "Compliant | Non-Compliant | Partially Compliant | Not Assessed",
          "issues": [
            {{
              "severity": "High | Medium | Low",
              "description": "Concise description (one sentence)",
              "document_reference": "Direct quote or paraphrase from the document",
              "recommendation": "Concise remediation action (one sentence)"
            }}
          ],
          "summary": "One short sentence compliance status summary"
        }}
      ],
      "total_issues": {{
        "high": <integer>,
        "medium": <integer>,
        "low": <integer>
      }},
      "key_recommendations": []
    }}

    ## Document to Analyse
    ---
    {document_text}
    ---

    Analyse EVERY one of the 11 obligations. If a document has no content relevant to a particular obligation, mark it as "Not Assessed" with an empty issues list and a note in the summary. Be brief, specific, cite the document, and do not write long paragraphs.
    """).strip()

    return prompt


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def analyse_document(document_text: str) -> dict[str, Any]:
    """
    Send the document text to Gemini and return a parsed compliance report dict.

    Args:
        document_text: The full extracted text of the document.

    Returns:
        A dictionary matching the PDPA compliance report schema.

    Raises:
        EnvironmentError: If the Gemini API key is not configured.
        RuntimeError: If the Gemini API call fails or the response cannot be parsed.
    """
    if not document_text or not document_text.strip():
        raise ValueError("Document text is empty. Nothing to analyse.")

    model = _get_gemini_client()
    prompt = _build_prompt(document_text)

    logger.info(
        "Sending document (%d characters) to Gemini for PDPA analysis...",
        len(document_text),
    )

    _MAX_ATTEMPTS = 3
    _RETRY_DELAY_SECONDS = 10

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = model.generate_content(prompt)
            break  # success — exit the retry loop
        except Exception as exc:
            exc_str = str(exc).lower()
            is_retryable = (
                "timeout" in exc_str
                or "503" in exc_str
                or "service unavailable" in exc_str
                or "deadline" in exc_str
            )
            if is_retryable and attempt < _MAX_ATTEMPTS:
                logger.warning(
                    "Gemini API call failed (attempt %d/%d): %s — retrying in %ds...",
                    attempt,
                    _MAX_ATTEMPTS,
                    exc,
                    _RETRY_DELAY_SECONDS,
                )
                time.sleep(_RETRY_DELAY_SECONDS)
                last_exc = exc
            else:
                raise RuntimeError(f"Gemini API request failed: {exc}") from exc
    else:
        # All retries exhausted
        raise RuntimeError(
            f"Gemini API request failed after {_MAX_ATTEMPTS} attempts: {last_exc}"
        ) from last_exc

    raw_text: str = ""
    try:
        raw_text = response.text
    except Exception as exc:
        raise RuntimeError(
            f"Failed to extract text from Gemini response: {exc}"
        ) from exc

    if not raw_text or not raw_text.strip():
        raise RuntimeError(
            "Gemini returned an empty response. "
            "This may be due to content filtering or a quota issue."
        )

    # Parse the JSON response
    result = _parse_json_response(raw_text)
    logger.info(
        "Analysis complete. Overall risk: %s | Issues — High: %s, Medium: %s, Low: %s",
        result.get("overall_risk_level", "Unknown"),
        result.get("total_issues", {}).get("high", 0),
        result.get("total_issues", {}).get("medium", 0),
        result.get("total_issues", {}).get("low", 0),
    )

    # Enrich each breached obligation with matching PDPC case precedents
    _attach_precedent_cases(result)

    # Generate a prioritised key recommendations list from all High issues
    _generate_key_recommendations(result)

    return result


def _attach_precedent_cases(result: dict[str, Any]) -> None:
    """
    For every obligation that has issues, look up matching PDPC enforcement
    cases and attach them as a 'precedent_cases' list on the obligation dict.
    Obligations with no issues receive an empty list.
    """
    for obligation in result.get("obligations", []):
        if obligation.get("issues"):
            cases = get_cases_for_obligation(obligation.get("obligation_name", ""))
            obligation["precedent_cases"] = format_cases_for_report(cases)
            if obligation["precedent_cases"]:
                logger.debug(
                    "Attached %d precedent case(s) to obligation '%s'.",
                    len(obligation["precedent_cases"]),
                    obligation.get("obligation_name"),
                )
        else:
            obligation["precedent_cases"] = []


# Obligation name fragments → (priority_rank, urgency)
# Matched case-insensitively against the obligation_name from Gemini's response.
_PRIORITY_MAP: list[tuple[tuple[str, ...], int, str]] = [
    # Priority 1 — immediate legal violations
    (("breach",),                        1, "Immediate"),
    (("consent",),                       1, "Immediate"),
    (("do not call", "dnc"),             1, "Immediate"),
    # Priority 2 — critical security risk
    (("protection",),                    2, "Short-term"),
    # Priority 3 — financial / contractual exposure
    (("transfer",),                      3, "Medium-term"),
    (("retention",),                     3, "Medium-term"),
    (("accountability",),                3, "Medium-term"),
    (("purpose",),                       3, "Medium-term"),
    (("notification",),                  3, "Medium-term"),
    (("accuracy",),                      3, "Medium-term"),
    (("access",),                        3, "Medium-term"),
]


def _classify_obligation(obligation_name: str) -> tuple[int, str]:
    """Return (priority_rank, urgency) for the given obligation name."""
    name_lower = obligation_name.lower()
    for keywords, rank, urgency in _PRIORITY_MAP:
        if any(kw in name_lower for kw in keywords):
            return rank, urgency
    return 3, "Medium-term"   # default


def _generate_key_recommendations(result: dict[str, Any]) -> None:
    """
    Build a prioritised list of key recommendations from all High-severity
    issues and write it back to result['key_recommendations'].

    Each recommendation is a dict with:
      priority_rank  : 1 | 2 | 3
      obligation_name: str
      action_required: str  (one clear sentence derived from the issue)
      urgency        : "Immediate" | "Short-term" | "Medium-term"

    Priority tiers:
      1 — Immediate legal violations (Data Breach Notification, Consent, DNC)
      2 — Critical security risk (Protection Obligation failures)
      3 — Financial / contractual exposure (Transfer, Retention, Accountability, etc.)

    Within each tier, recommendations are ordered by priority_rank.
    """
    raw_recs: list[dict[str, Any]] = []

    for obligation in result.get("obligations", []):
        ob_name = obligation.get("obligation_name", "Unknown")
        high_issues = [
            iss for iss in obligation.get("issues", [])
            if iss.get("severity") == "High"
        ]
        if not high_issues:
            continue

        rank, urgency = _classify_obligation(ob_name)

        # Generate a separate recommendation for every High-severity issue
        for issue in high_issues:
            action = issue.get("recommendation", "").strip()
            if action and not action[0].isupper():
                action = action.capitalize()

            raw_recs.append({
                "priority_rank":   rank,
                "obligation_name": ob_name,
                "action_required": action if action else f"Remediate High-severity {ob_name} issue immediately.",
                "urgency":         urgency,
            })

    # Sort by priority_rank ASC
    raw_recs.sort(key=lambda r: r["priority_rank"])

    result["key_recommendations"] = raw_recs
    logger.info(
        "Generated %d key recommendation(s) from High-severity issues.",
        len(raw_recs),
    )


def _parse_json_response(raw_text: str) -> dict[str, Any]:
    """
    Parse and validate the JSON response from Gemini.

    Strategy:
      1. Strip markdown code fences.
      2. Attempt direct JSON parse.
      3. On failure, attempt to repair truncated JSON (close open
         brackets/strings) and retry.
      4. If repair also fails, save the raw response to raw_response.txt
         so the data is not lost, then raise.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present (e.g., ```json ... ```)
    fence_pattern = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
    match = fence_pattern.match(text)
    if match:
        text = match.group(1).strip()

    # Attempt 1: direct parse
    try:
        data = json.loads(text)
        return _validate_schema(data)
    except json.JSONDecodeError as first_exc:
        logger.warning(
            "Initial JSON parse failed at position %d: %s — attempting repair...",
            first_exc.pos,
            first_exc.msg,
        )

    # Attempt 2: repair truncated JSON and retry
    repaired = _repair_json(text)
    try:
        data = json.loads(repaired)
        logger.info("JSON repair succeeded — truncated response was recovered.")
        return _validate_schema(data)
    except json.JSONDecodeError as exc:
        # All parse attempts failed — persist the raw response before raising
        saved_path = _save_raw_response(raw_text)
        raise RuntimeError(
            f"Failed to parse Gemini response as JSON even after repair "
            f"(column {exc.colno}, line {exc.lineno}): {exc.msg}. "
            f"Raw response saved to '{saved_path}' for manual inspection."
        ) from exc


def _validate_schema(data: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure the parsed dict has all required top-level keys.

    Rather than hard-failing on missing optional fields, this function
    computes or defaults them so the pipeline can continue:
      - 'obligations' is the only truly required field (raises if absent).
      - 'total_issues' is recomputed from obligations if missing.
      - 'document_summary', 'overall_risk_level', 'overall_risk_justification',
        and 'key_recommendations' are given sensible defaults if absent.
    """
    # The one field we cannot recover without
    if "obligations" not in data:
        raise RuntimeError(
            "Gemini response is missing the 'obligations' field — "
            "the model did not follow the required output format. "
            "Check raw_response.txt if it was saved."
        )

    # Recompute total_issues from the obligations list if the model omitted it
    if "total_issues" not in data:
        high = medium = low = 0
        for ob in data.get("obligations", []):
            for issue in ob.get("issues", []):
                sev = issue.get("severity", "")
                if sev == "High":
                    high += 1
                elif sev == "Medium":
                    medium += 1
                elif sev == "Low":
                    low += 1
        data["total_issues"] = {"high": high, "medium": medium, "low": low}
        logger.warning(
            "Field 'total_issues' was missing from the Gemini response — "
            "recomputed as H:%d M:%d L:%d from obligations.",
            high, medium, low,
        )

    # Default other optional top-level fields
    data.setdefault("document_summary", "No summary provided.")
    data.setdefault("overall_risk_level", "Unknown")
    data.setdefault("overall_risk_justification", "Not provided.")
    data.setdefault("key_recommendations", [])

    return data



def _repair_json(text: str) -> str:
    """
    Attempt to close a truncated JSON string by:
      - Truncating any trailing incomplete key, string value, or object fragment.
      - Restoring a valid structure and closing all open brackets/braces in order.
    """
    # 1. First, attempt to locate the last complete element or key-value pair.
    # We walk character by character to find the balance and keep track of state.
    stack: list[str] = []
    in_string = False
    escape_next = False
    last_good_pos = 0

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            if in_string:
                escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            if not in_string:
                # We just closed a string. If we're not inside any incomplete property,
                # this position is a potential safe recovery point.
                last_good_pos = i + 1
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            stack.append('}' if ch == '{' else ']')
            last_good_pos = i + 1
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()
                last_good_pos = i + 1

    # If the JSON parsed successfully all the way, return it as-is
    if not stack and not in_string:
        return text

    # Truncate to the last character that was part of a balanced structure or completed token
    # to avoid trailing garbage like half-written keys/values.
    truncated = text[:last_good_pos].rstrip()

    # Clean up trailing punctuation like commas, colons, brackets
    while truncated and truncated[-1] in (',', ':', '{', '['):
        # If we remove an opening bracket, we also remove the expected closing bracket from our stack
        if truncated[-1] in ('{', '['):
            if stack:
                stack.pop()
        truncated = truncated[:-1].rstrip()

    # Re-calculate stack for the truncated string
    stack = []
    in_string = False
    escape_next = False
    for ch in truncated:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ('{', '['):
            stack.append('}' if ch == '{' else ']')
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()

    # Close all unclosed structures in reverse order
    result = truncated + ''.join(reversed(stack))
    return result


def _save_raw_response(raw_text: str, filename: str = "raw_response.txt") -> str:
    """
    Write the raw Gemini response to a file so it is not lost when parsing fails.
    Returns the path of the saved file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(raw_text)
        logger.info("Raw Gemini response saved to '%s'.", filename)
    except OSError as exc:
        logger.error("Could not save raw response to '%s': %s", filename, exc)
    return filename
