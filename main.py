"""
main.py
-------
Entry point for the PDPA Audit Bot.

Usage:
    python main.py <path_to_document>

Supported document types: .pdf, .docx, .txt

The Gemini API key must be set in a .env file as GEMINI_API_KEY.
"""

import argparse
import logging
import sys
import textwrap
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing modules
# that use environment variables.
load_dotenv()

from extractor import extract_text
from analyzer import analyse_document
from reporter import generate_reports

logger = logging.getLogger("pdpa_audit_bot.main")



# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

def _configure_logging(verbose: bool = False) -> None:
    """Set up console logging with an appropriate level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ---------------------------------------------------------------------------
# CLI argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdpa_audit_bot",
        description=(
            "PDPA Audit Bot — Analyses documents for compliance with Singapore's\n"
            "Personal Data Protection Act 2012 (as amended) using Google Gemini AI."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python main.py sample_policy.txt
          python main.py path/to/privacy_policy.pdf --output-dir my_reports
          python main.py path/to/contract.docx --verbose
        """).strip(),
    )
    parser.add_argument(
        "document",
        help="Path to the document to audit (.pdf, .docx, or .txt)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        metavar="DIR",
        help="Directory to write the compliance reports (default: ./reports)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser


# ---------------------------------------------------------------------------
# Console output helpers
# ---------------------------------------------------------------------------

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    _HAS_COLOR = True
except ImportError:
    _HAS_COLOR = False
    class Fore:  # type: ignore[override]
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = RESET = ""
    class Style:  # type: ignore[override]
        BRIGHT = RESET_ALL = ""



def _print_banner() -> None:
    banner = r"""
  ____  ____  ____   _    _             _ _ _     ____        _   
 |  _ \|  _ \|  _ \ / \  | |           | (_) |   | __ )  ___ | |_ 
 | |_) | | | | |_) / _ \ | |     ___   | |_| |_  |  _ \ / _ \| __|
 |  __/| |_| |  __/ ___ \| |___ |___| | |_| |  | | |_) | (_) | |_ 
 |_|   |____/|_| /_/   \_\_____|      |_|_|_|_| |____/ \___/ \__|
                                                                    
  Singapore PDPA Compliance Auditor — Powered by Google Gemini
"""
    if _HAS_COLOR:
        print(Fore.CYAN + Style.BRIGHT + banner + Style.RESET_ALL)
    else:
        print(banner)


def _print_step(step: str, message: str) -> None:
    prefix = f"[{step}]"
    if _HAS_COLOR:
        print(f"{Fore.CYAN}{Style.BRIGHT}{prefix}{Style.RESET_ALL} {message}")
    else:
        print(f"{prefix} {message}")


def _print_success(message: str) -> None:
    if _HAS_COLOR:
        print(f"{Fore.GREEN}{Style.BRIGHT}✓{Style.RESET_ALL}  {message}")
    else:
        print(f"[OK] {message}")


def _print_error(message: str) -> None:
    if _HAS_COLOR:
        print(f"{Fore.RED}{Style.BRIGHT}✗  ERROR:{Style.RESET_ALL} {message}", file=sys.stderr)
    else:
        print(f"[ERROR] {message}", file=sys.stderr)


def _print_summary(json_path: str, txt_path: str, result: dict) -> None:
    total = result.get("total_issues", {})
    risk = result.get("overall_risk_level", "Unknown")

    risk_colours = {
        "High":   Fore.RED,
        "Medium": Fore.YELLOW,
        "Low":    Fore.GREEN,
    }
    risk_colour = risk_colours.get(risk, Fore.WHITE) if _HAS_COLOR else ""

    print()
    print("=" * 60)
    if _HAS_COLOR:
        print(f"  {Style.BRIGHT}AUDIT COMPLETE{Style.RESET_ALL}")
    else:
        print("  AUDIT COMPLETE")
    print("=" * 60)
    print(f"  Overall Risk : {risk_colour}{Style.BRIGHT if _HAS_COLOR else ''}{risk}{Style.RESET_ALL if _HAS_COLOR else ''}")
    print(f"  Issues Found : 🔴 High {total.get('high', 0)} | 🟡 Medium {total.get('medium', 0)} | 🟢 Low {total.get('low', 0)}")
    print()
    print(f"  📄 JSON Report : {json_path}")
    print(f"  📋 TXT Report  : {txt_path}")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Main entry point. Returns 0 on success, non-zero on failure.
    """
    parser = _build_parser()
    args = parser.parse_args()
    _configure_logging(verbose=args.verbose)

    _print_banner()

    # ── Pre-processing notice and consent ───────────────────────────────────
    print("================================================================================")
    print("  PRIVACY AND DATA PROCESSING NOTICE")
    print("--------------------------------------------------------------------------------")
    print("  • The document will be analysed by Google Gemini AI.")
    print("  • Processing occurs in Google Cloud Singapore (asia-southeast1).")
    print("  • The document is not stored by this tool after analysis.")
    print("  • Reports are saved locally to the /reports folder.")
    print("  • This tool does not constitute legal advice.")
    print("================================================================================")
    try:
        consent = input("Do you consent to proceed? (yes/no): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        print("Analysis cancelled. No data was processed.")
        return 0

    if consent not in ["yes", "y"]:
        print("Analysis cancelled. No data was processed.")
        return 0
    print()

    document_path = args.document

    # ── Step 1: Validate the input file ──────────────────────────────────────
    _print_step("1/4", f"Validating input file: {document_path}")

    supported_extensions = {".pdf", ".docx", ".txt"}
    path = Path(document_path)

    if not path.exists():
        _print_error(f"File not found: {document_path}")
        return 1

    if path.suffix.lower() not in supported_extensions:
        _print_error(
            f"Unsupported file type '{path.suffix}'. "
            f"Supported: {', '.join(sorted(supported_extensions))}"
        )
        return 1

    _print_success(f"File validated: {path.name} ({path.stat().st_size:,} bytes)")

    # ── Step 2: Extract text ──────────────────────────────────────────────────
    _print_step("2/4", "Extracting text from document...")

    try:
        document_text = extract_text(document_path)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        _print_error(str(exc))
        return 1

    _print_success(f"Extracted {len(document_text):,} characters of text.")

    # ── Step 3: Analyse with Gemini ───────────────────────────────────────────
    _print_step("3/4", "Analysing document against all 11 PDPA obligations (this may take a moment)...")

    try:
        analysis_result = analyse_document(document_text)
    except EnvironmentError as exc:
        _print_error(str(exc))
        _print_error(
            "Ensure your .env file contains:\n"
            "  GOOGLE_CLOUD_PROJECT=your-gcp-project-id\n"
            "  GOOGLE_CLOUD_REGION=asia-southeast1\n"
            "  GEMINI_MODEL=gemini-2.5-flash"
        )
        return 1
    except (ValueError, RuntimeError) as exc:
        _print_error(str(exc))
        return 1

    _print_success("Analysis complete.")

    # ── Step 4: Generate reports ──────────────────────────────────────────────
    _print_step("4/4", f"Generating compliance reports in '{args.output_dir}/'...")

    try:
        json_path, txt_path = generate_reports(
            analysis_result=analysis_result,
            source_file=document_path,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        _print_error(f"Failed to write reports: {exc}")
        return 1

    _print_success("Reports written successfully.")

    # ── Report retention with auto-deletion ─────────────────────────────────
    try:
        reports_dir = Path(args.output_dir)
        if reports_dir.exists() and reports_dir.is_dir():
            deleted_count = 0
            now = time.time()
            cutoff = now - (30 * 24 * 60 * 60)  # 30 days in seconds

            # Scan the reports directory for report files
            for file_path in reports_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in (".json", ".txt"):
                    mtime = file_path.stat().st_mtime
                    if mtime < cutoff:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except OSError as e:
                            logger.error("Failed to delete %s: %s", file_path, e)

            if deleted_count > 0:
                print(f"INFO retention: Deleted {deleted_count} report(s) older than 30 days")
            else:
                print("INFO retention: No expired reports found")
    except Exception as exc:
        logger.error("Error during report retention check: %s", exc)

    _print_summary(json_path, txt_path, analysis_result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
