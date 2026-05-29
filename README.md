# PDPA Audit Bot 🛡️

An AI-powered compliance screening tool that analyses documents against all 11 obligations of the Singapore Personal Data Protection Act 2012 (as amended 2020).

Built with Google Gemini via Vertex AI, grounded in official PDPC advisory guidelines and real enforcement decisions.

> ⚠️ **Disclaimer:** This tool is an AI-powered screening aid and does not constitute legal advice. All findings should be verified by a qualified data protection professional or legal counsel before any compliance action is taken.

---

## What it does

- Accepts a document (TXT, PDF, or DOCX) as input
- Analyses the content against all 11 PDPA obligations
- Flags compliance issues with severity ratings (High / Medium / Low)
- Cites real PDPC enforcement decisions as precedents for each breach found
- Outputs a structured JSON report and a human-readable TXT audit report
- Prioritises remediation actions into 3 tiers (Immediate / Short-term / Medium-term)

---

## The 11 PDPA obligations covered

| # | Obligation | PDPA Section |
|---|---|---|
| 1 | Purpose Limitation | Section 18 |
| 2 | Notification | Section 20 |
| 3 | Consent | Sections 13–17 |
| 4 | Access and Correction | Sections 21–22 |
| 5 | Accuracy | Section 23 |
| 6 | Protection | Section 24 |
| 7 | Retention Limitation | Section 25 |
| 8 | Transfer Limitation | Section 26 |
| 9 | Data Breach Notification | Sections 26A–26F |
| 10 | Accountability | Section 11 |
| 11 | Do Not Call (DNC) Registry | Part IX |

---

## Reference sources

This tool is grounded in two authoritative sources — not just AI training memory:

- **PDPC Advisory Guidelines on Key Concepts in the PDPA** (Revised 16 May 2022) — defines what each obligation requires
- **Real PDPC Enforcement Decisions** — 38 actual cases from 2017–2023 with citations, penalties, and breach summaries

Case precedents are sourced from publicly available PDPC enforcement decisions published at [pdpc.gov.sg/enforcement-decisions](https://www.pdpc.gov.sg/enforcement-decisions)

---

## Data sovereignty

This tool uses **Google Gemini via Vertex AI** with processing locked to:

```
Region: asia-southeast1 (Singapore)
```

Google Cloud stores and processes data only in the specified region. This means all document analysis stays within Singapore, directly addressing the PDPA Transfer Limitation Obligation for users processing Singapore personal data.

---

## Sample output

```
================================================================================
  PDPA COMPLIANCE AUDIT REPORT
  Singapore Personal Data Protection Act 2012 (as amended)
================================================================================
  Overall Risk     : 🔴 High
  Issues Found     : 🔴 High 20 | 🟡 Medium 3 | 🟢 Low 0

  KEY RECOMMENDATIONS (Priority Actions)
  ┌──────────────────────────────────────────┐
  │  PRIORITY 1 — Immediate Legal Violation  │
  └──────────────────────────────────────────┘
  [01] 🔴 Consent Obligation — Implement consent withdrawal mechanism
  [02] 🔴 Data Breach Notification — Develop mandatory breach response plan
  [03] 🔴 DNC Registry — Implement mandatory DNC checks before marketing

  RELEVANT PRECEDENTS
  · Neo Yong Xiang [2021] SGPDPC 12 — S$35,000 (Consent breach)
  · Commeasure Pte Ltd [2021] SGPDPC 11 — S$74,000 (Protection breach)
================================================================================
```

---

## Project structure

```
pdpa_audit_bot/
├── main.py                  # Entry point — CLI, consent notice, orchestration
├── extractor.py             # Document text extraction (TXT, PDF, DOCX)
├── analyzer.py              # Gemini API call via Vertex AI (asia-southeast1)
├── reporter.py              # JSON and TXT report generation
├── pdpa_reference.py        # All 11 PDPA obligations — official definitions
├── pdpa_cases.py            # 38 real PDPC enforcement cases database
├── PRIVACY_NOTICE.md        # Privacy notice for users of this tool
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── reports/                 # Generated audit reports (auto-deleted after 30 days)
```

---

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud project with Vertex AI API enabled
- `gcloud` CLI authenticated

### 1. Enable Vertex AI on your GCP project

```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
```

### 2. Authenticate

```bash
gcloud auth application-default login
```

### 3. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/pdpa-audit-bot
cd pdpa-audit-bot
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_REGION=asia-southeast1
GEMINI_MODEL=gemini-2.5-flash
```

### 5. Run

```bash
python main.py your_document.txt
```

Supported formats: `.txt`, `.pdf`, `.docx`

---

## Usage

```bash
# Analyse a privacy policy
python main.py privacy_policy.txt

# Analyse a PDF
python main.py data_protection_policy.pdf

# Analyse a Word document
python main.py employee_handbook.docx
```

On first run, you will see a consent notice and must type `yes` or `y` to proceed.

Reports are saved to the `/reports` folder as both `.json` and `.txt`. Reports older than 30 days are automatically deleted.

---

## Red team results

This tool was systematically red-teamed before release:

| Test | Result |
|---|---|
| Prompt injection via document content | ✅ Passed — injected instructions ignored |
| Hallucination on compliant document | ✅ Passed — no invented violations |
| Empty file | ✅ Handled gracefully |
| Gibberish input | ✅ Handled gracefully |
| Minimal content file | ✅ Handled gracefully |
| Large file (110,000 chars) | ✅ No timeout or crash |
| Non-English content | ✅ Handled gracefully |
| Governance self-assessment | ✅ All gaps identified and remediated |

---

## Governance alignment

This project is aligned with the **IMDA Model AI Governance Framework 
for Agentic AI (v1.5, May 2026)** and the **PDPA 2012 (as amended)**:

| IMDA MGF Dimension | Implementation in this project |
|---|---|
| Assess and bound risks upfront | Red-teamed across 8 test categories before release; scope limited to screening only |
| Make humans meaningfully accountable | All findings require professional verification; AI-generated caveat on every report |
| Implement technical controls | Vertex AI locked to asia-southeast1; consent notice before processing; 30-day report auto-deletion |
| Enable end-user responsibility | Full disclaimer, PDPC source attribution, and PRIVACY_NOTICE.md published |

---

## Limitations

- This is a **screening tool**, not a substitute for legal advice
- Analysis quality depends on the completeness of the input document
- Case precedent database covers 2017–2023 decisions; newer cases may not be included
- The tool analyses text content only — it cannot assess actual organisational practices

---

## Portfolio context

This project was built as part of a self-directed AI governance portfolio aligned to:

- PDPC Practitioner Certificate

Built using **Google Antigravity** (agentic IDE) with **Claude Sonnet 4.6** as the development agent.

---

## Author

**Chan** — Data Analytics & Cybersecurity professional transitioning into AI Governance
Singapore | [GitHub](https://github.com/AIknowlah) | [LinkedIn](https://linkedin.com/in/AIKnowlah)

---

## Disclaimer

This tool is AI-generated using Google Gemini and is grounded in the PDPC Advisory Guidelines on Key Concepts in the PDPA (Revised 16 May 2022) and real PDPC enforcement decisions. It does not constitute legal advice. Findings should be verified by a qualified data protection professional or legal counsel before any compliance action is taken. For the latest regulatory guidance, refer to [pdpc.gov.sg](https://www.pdpc.gov.sg).

Case precedents cited in reports are sourced from publicly available PDPC enforcement decisions at [pdpc.gov.sg/enforcement-decisions](https://www.pdpc.gov.sg/enforcement-decisions).
