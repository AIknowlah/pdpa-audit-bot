"""
PDPA Reference Module
Source: PDPC Advisory Guidelines on Key Concepts in the PDPA (Revised 16 May 2022)
This module provides authoritative reference text for all 11 PDPA obligations.
Used to ground the AI analysis in official PDPC guidance rather than training memory.
"""

PDPA_OBLIGATIONS = {
    "1_purpose_limitation": {
        "name": "Purpose Limitation Obligation",
        "section": "Section 18, PDPA 2012",
        "requirement": (
            "An organisation may collect, use or disclose personal data only for purposes "
            "that a reasonable person would consider appropriate in the circumstances, and "
            "for which the individual has been notified or has given consent. Organisations "
            "must not use personal data for purposes beyond what was communicated to the individual."
        ),
        "key_tests": [
            "Are all data collection purposes clearly stated and specific?",
            "Are purposes limited to what is necessary for the stated function?",
            "Does the policy avoid vague catch-all phrases like 'any other purposes we deem appropriate'?",
            "Is secondary use of data communicated and consented to?"
        ]
    },
    "2_notification": {
        "name": "Notification Obligation",
        "section": "Section 20, PDPA 2012",
        "requirement": (
            "Before collecting, using or disclosing personal data, an organisation must notify "
            "individuals of the purposes for which data is being collected, used or disclosed. "
            "Notification must be given in a clear and accessible manner."
        ),
        "key_tests": [
            "Are individuals notified before or at the time of data collection?",
            "Is the notification clear and written in plain language?",
            "Does the notification cover all purposes for which data will be used?",
            "Is there a Data Protection Policy accessible to individuals?"
        ]
    },
    "3_consent": {
        "name": "Consent Obligation",
        "section": "Sections 13-17, PDPA 2012",
        "requirement": (
            "An organisation must obtain the consent of an individual before collecting, using "
            "or disclosing personal data. Consent must be voluntary, informed and given for "
            "specific purposes. Deemed consent and legitimate interests exceptions apply in "
            "specific circumstances as amended in 2020."
        ),
        "key_tests": [
            "Is consent obtained before data collection?",
            "Is consent specific to identified purposes?",
            "Are individuals able to withdraw consent?",
            "Is deemed consent being relied upon appropriately?",
            "Are minors' consent handled appropriately?"
        ]
    },
    "4_access_correction": {
        "name": "Access and Correction Obligation",
        "section": "Sections 21-22, PDPA 2012",
        "requirement": (
            "Organisations must provide individuals with access to their personal data upon "
            "request, and must correct any errors or omissions within a reasonable time. "
            "Organisations must respond to access requests within 30 days."
        ),
        "key_tests": [
            "Is there a process for individuals to request access to their data?",
            "Is there a process for individuals to request correction of their data?",
            "Can requests be responded to within 30 days?",
            "Are fees for access requests reasonable and disclosed upfront?"
        ]
    },
    "5_accuracy": {
        "name": "Accuracy Obligation",
        "section": "Section 23, PDPA 2012",
        "requirement": (
            "Organisations must make reasonable effort to ensure that personal data collected "
            "is accurate and complete, especially if it is likely to be used to make a decision "
            "that affects the individual, or disclosed to another organisation."
        ),
        "key_tests": [
            "Are processes in place to verify data accuracy at collection?",
            "Is there a mechanism for individuals to update their data?",
            "Are data accuracy checks performed before using data for decisions?"
        ]
    },
    "6_protection": {
        "name": "Protection Obligation",
        "section": "Section 24, PDPA 2012",
        "requirement": (
            "Organisations must protect personal data in their possession or under their control "
            "by making reasonable security arrangements to prevent unauthorised access, collection, "
            "use, disclosure, copying, modification, disposal or similar risks."
        ),
        "key_tests": [
            "Are reasonable technical and organisational security measures in place?",
            "Are access controls implemented (least privilege principle)?",
            "Are data handling procedures documented and enforced?",
            "Are third-party vendors and data processors contractually bound to protect data?",
            "Are regular security assessments conducted?"
        ]
    },
    "7_retention_limitation": {
        "name": "Retention Limitation Obligation",
        "section": "Section 25, PDPA 2012",
        "requirement": (
            "Organisations must cease to retain personal data, or remove the means by which "
            "personal data can be associated with particular individuals, as soon as it is "
            "reasonable to assume that the purpose for collection is no longer served."
        ),
        "key_tests": [
            "Is a data retention schedule defined?",
            "Are retention periods proportionate to the purposes?",
            "Is data securely deleted or anonymised when retention period expires?",
            "Is there a process for reviewing and disposing of data no longer needed?"
        ]
    },
    "8_transfer_limitation": {
        "name": "Transfer Limitation Obligation",
        "section": "Section 26, PDPA 2012",
        "requirement": (
            "Organisations must not transfer personal data outside Singapore unless the "
            "recipient country provides a standard of protection comparable to the PDPA, "
            "or the transfer is subject to legally enforceable obligations (contracts, "
            "binding corporate rules, etc.)."
        ),
        "key_tests": [
            "Are cross-border data transfers identified and documented?",
            "Is the recipient country's data protection standard assessed?",
            "Are contractual clauses or binding corporate rules in place for transfers?",
            "Are third-party cloud providers' data residency locations documented?"
        ]
    },
    "9_data_breach_notification": {
        "name": "Data Breach Notification Obligation",
        "section": "Sections 26A-26F, PDPA 2012 (2020 Amendment)",
        "requirement": (
            "Organisations must notify the PDPC of data breaches that are likely to result "
            "in significant harm to affected individuals within 3 calendar days of assessment. "
            "Affected individuals must also be notified without undue delay where the breach "
            "is likely to result in significant harm."
        ),
        "key_tests": [
            "Is there a documented data breach response plan?",
            "Are breach assessment procedures in place (3-day notification window)?",
            "Is there a process to notify affected individuals?",
            "Are breach incidents logged and reviewed?"
        ]
    },
    "10_accountability": {
        "name": "Accountability Obligation",
        "section": "Section 11, PDPA 2012",
        "requirement": (
            "Organisations must designate one or more individuals (Data Protection Officers) "
            "to be responsible for ensuring the organisation complies with the PDPA. "
            "Organisations must implement data protection policies and practices, and make "
            "contact information of the DPO available to the public."
        ),
        "key_tests": [
            "Is a Data Protection Officer (DPO) designated?",
            "Is the DPO's contact information publicly available?",
            "Are staff trained on PDPA obligations?",
            "Are data protection policies documented and communicated internally?",
            "Are third-party data processors contractually obligated to PDPA standards?"
        ]
    },
    "11_do_not_call": {
        "name": "Do Not Call (DNC) Registry Obligation",
        "section": "Part IX, PDPA 2012",
        "requirement": (
            "Organisations must check the DNC registry before sending marketing messages "
            "to Singapore telephone numbers. Organisations must not send unsolicited "
            "telemarketing messages to numbers registered on the DNC registry unless "
            "clear and unambiguous consent has been obtained."
        ),
        "key_tests": [
            "Are marketing messages sent only after DNC registry checks?",
            "Is consent for marketing communications obtained separately and clearly?",
            "Are records of DNC checks maintained?",
            "Are opt-out requests for marketing communications honoured?"
        ]
    }
}

def get_reference_prompt() -> str:
    """Returns a formatted reference text for injection into the Gemini prompt."""
    lines = [
        "AUTHORITATIVE PDPA REFERENCE (Source: PDPC Advisory Guidelines, Revised 16 May 2022)",
        "="*70,
        "You MUST check the document against these 11 obligations ONLY.",
        "Do not rely on general training knowledge. Use only these definitions.",
        ""
    ]
    for key, ob in PDPA_OBLIGATIONS.items():
        lines.append(f"OBLIGATION: {ob['name']} ({ob['section']})")
        lines.append(f"REQUIREMENT: {ob['requirement']}")
        lines.append("KEY COMPLIANCE TESTS:")
        for test in ob['key_tests']:
            lines.append(f"  - {test}")
        lines.append("")
    return "\n".join(lines)
