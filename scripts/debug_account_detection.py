#!/usr/bin/env python3
"""Debug account boundary detection step by step."""

import sys

sys.path.insert(0, "./src")

from bank_statement_separator.utils.pdf_processor import PDFProcessor
import re


def debug_account_detection(pdf_path):
    """Debug account boundary detection logic step by step."""

    # Extract text
    processor = PDFProcessor()
    pdf_doc = processor.extract_text_from_pdf(pdf_path)
    text_chunks = [page.text for page in pdf_doc.pages]
    combined_text = " ".join(text_chunks)
    total_pages = len(text_chunks)

    print(f"📄 PDF: {pdf_path}")
    print(f"📊 Total pages: {total_pages}")
    print(f"📊 Total text length: {len(combined_text)} characters")
    print("\n" + "=" * 60)

    # Test the account boundary detection method directly
    # Use the same logic as in the method
    account_patterns = [
        r"(?i)(?:account|card)\s*(?:number|no\.?|#)?\s*[:]\s*(\d[\d\s\-]{8,})",  # With colon
        r"(?i)(?:account|card)\s*(?:number|no\.?|#)\s*[:]\s*(\d[\d\s\-]{8,})",  # Without optional colon
        r"(?i)(?:account|card)\s*(?:number|no\.?|#)?\s+(\d[\d\s\-]{8,})",  # Space separated
        r"(?i)account\s*number\s*:\s*(\d[\d\s\-]{8,})",  # Explicit "Account Number:"
        r"(?i)account\s*number\s+(\d[\d\s\-]{8,})",  # "Account Number" without colon
    ]

    # Find matches using all patterns, avoiding duplicates
    account_matches = []
    seen_positions = set()

    print("🔍 PATTERN MATCHING:")
    for i, pattern in enumerate(account_patterns):
        matches = list(re.finditer(pattern, combined_text))
        print(f"Pattern {i + 1}: Found {len(matches)} matches")
        for match in matches:
            if match.start() not in seen_positions:
                account_matches.append(match)
                seen_positions.add(match.start())
                print(
                    f"  ✅ Added: pos={match.start()}, account='{match.group(1).strip()}'"
                )
            else:
                print(f"  ❌ Duplicate at pos={match.start()}, skipped")

    print(f"\n📋 UNIQUE MATCHES: {len(account_matches)}")

    # Process matches like the real method
    unique_accounts = {}
    for match in account_matches:
        account = re.sub(r"[\s\-]", "", match.group(1))  # Remove spaces and dashes
        if len(account) >= 8:  # Valid account length
            char_pos = match.start()
            text_progress = char_pos / len(combined_text)
            estimated_page = max(
                1, min(total_pages, int(text_progress * total_pages) + 1)
            )

            print(f"\n🔍 Processing account: {account}")
            print(f"   Position: {char_pos} -> Page: {estimated_page}")

            # Check deduplication logic
            is_new_account = account not in unique_accounts
            if not is_new_account:
                existing_pos = unique_accounts.get(account)
                if existing_pos is not None:
                    position_diff = abs(char_pos - existing_pos)
                    threshold = len(combined_text) * 0.2
                    print(
                        f"   Account exists at {existing_pos}, diff={position_diff}, threshold={threshold}"
                    )
                    if position_diff > threshold:
                        is_new_account = True
                        print("   ✅ Position difference significant, treating as new")
                    else:
                        print("   ❌ Position too close, skipping")

            if is_new_account:
                unique_accounts[account] = char_pos
                print("   ✅ Added to unique_accounts")
            else:
                print("   ❌ Skipped (duplicate)")

    print(f"\n📋 FINAL UNIQUE ACCOUNTS: {len(unique_accounts)}")
    for account, pos in unique_accounts.items():
        est_page = max(1, int((pos / len(combined_text)) * total_pages))
        print(f"  - {account} at position {pos} (page {est_page})")

    # Create boundaries
    boundaries = []
    for account, char_pos in unique_accounts.items():
        estimated_page = max(1, int((char_pos / len(combined_text)) * total_pages))
        boundaries.append(
            {
                "account": account,
                "page": estimated_page,
                "confidence": 0.7,
                "char_pos": char_pos,
            }
        )

    boundaries = sorted(boundaries, key=lambda x: x["char_pos"])

    print(f"\n📋 BOUNDARIES CREATED: {len(boundaries)}")
    for b in boundaries:
        print(f"  - Account: {b['account']}, Page: {b['page']}, Pos: {b['char_pos']}")

    return len(boundaries) >= 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_account_detection.py <pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    result = debug_account_detection(pdf_path)
    print(
        f"\n🏁 RESULT: {'✅ Multiple boundaries detected' if result else '❌ Insufficient boundaries'}"
    )
