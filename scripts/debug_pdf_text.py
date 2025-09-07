#!/usr/bin/env python3
"""Extract and examine text from test PDF to debug pattern matching."""

import sys

sys.path.insert(0, "./src")

from bank_statement_separator.utils.pdf_processor import PDFProcessor
import re


def debug_pdf_text(pdf_path):
    """Extract text from PDF and analyze account patterns."""

    processor = PDFProcessor()

    try:
        # Extract text from PDF
        pdf_doc = processor.extract_text_from_pdf(pdf_path)
        text_chunks = [page.text for page in pdf_doc.pages]
        combined_text = " ".join(text_chunks)

        print(f"📄 PDF: {pdf_path}")
        print(f"📊 Total pages: {len(text_chunks)}")
        print(f"📊 Total text length: {len(combined_text)} characters")
        print("\n" + "=" * 80)

        # Show first 500 characters of each page
        for i, page_text in enumerate(text_chunks):
            print(f"\n📄 PAGE {i + 1} (first 500 chars):")
            print("-" * 40)
            print(repr(page_text[:500]))
            print("-" * 40)

        print("\n🔍 COMBINED TEXT (first 1000 chars):")
        print("-" * 40)
        print(repr(combined_text[:1000]))
        print("-" * 40)

        # Test account patterns
        account_patterns = [
            r"(?i)(?:account|card)\s*(?:number|no\.?|#)?\s*[:]\s*(\d[\d\s\-]{8,})",  # With colon
            r"(?i)(?:account|card)\s*(?:number|no\.?|#)\s*[:]\s*(\d[\d\s\-]{8,})",  # Without optional colon
            r"(?i)(?:account|card)\s*(?:number|no\.?|#)?\s+(\d[\d\s\-]{8,})",  # Space separated
            r"(?i)account\s*number\s*:\s*(\d[\d\s\-]{8,})",  # Explicit "Account Number:"
            r"(?i)account\s*number\s+(\d[\d\s\-]{8,})",  # "Account Number" without colon
        ]

        print("\n🔍 ACCOUNT PATTERN MATCHING:")
        print("=" * 60)

        all_matches = []
        for i, pattern in enumerate(account_patterns):
            matches = list(re.finditer(pattern, combined_text))
            print(f"\nPattern {i + 1}: {pattern}")
            print(f"Found {len(matches)} matches:")

            for match in matches:
                account = re.sub(r"[\s\-]", "", match.group(1))
                print(f"  - Full match: '{match.group(0)}'")
                print(f"    Account number: '{match.group(1)}' -> '{account}'")
                print(f"    Position: {match.start()}-{match.end()}")
                all_matches.append((account, match.start()))

        print("\n📋 SUMMARY:")
        print(
            f"Total unique accounts found: {len(set(acc for acc, pos in all_matches))}"
        )
        unique_accounts = set(acc for acc, pos in all_matches)
        for acc in sorted(unique_accounts):
            print(f"  - {acc}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_pdf_text.py <pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    debug_pdf_text(pdf_path)
