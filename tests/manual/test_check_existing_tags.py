#!/usr/bin/env python3
"""
Check existing tags in Paperless instance and recommend error tags to create.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def main():
    """Check existing tags and recommend error tags to create."""
    print("🔍 Checking Existing Paperless Tags")
    print("=" * 40)

    # Load configuration
    config = load_config()
    config.paperless_enabled = True

    print(f"📋 Paperless URL: {config.paperless_url}")
    print()

    # Connect to Paperless
    client = PaperlessClient(config)

    if not client.is_enabled():
        print("❌ Paperless client not enabled")
        return

    try:
        # Try to get existing tags
        print("🏷️  Fetching existing tags from Paperless...")

        # Use the existing method to get tags
        import httpx

        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.get(
                f"{config.paperless_url.rstrip('/')}/api/tags/", headers=client.headers
            )
            response.raise_for_status()

            tags_data = response.json()
            existing_tags = tags_data.get("results", [])

            print(f"✅ Found {len(existing_tags)} existing tags:")
            print()

            # Show existing tags
            for tag in existing_tags[:10]:  # Show first 10
                tag_name = tag.get("name", "")
                tag_id = tag.get("id", "")
                print(f"  • {tag_name} (ID: {tag_id})")

            if len(existing_tags) > 10:
                print(f"  ... and {len(existing_tags) - 10} more tags")

            print()

            # Check for test-related tags
            test_tags = [
                tag for tag in existing_tags if "test" in tag.get("name", "").lower()
            ]
            if test_tags:
                print("🧪 Existing test tags:")
                for tag in test_tags:
                    print(f"  • {tag['name']} (ID: {tag['id']})")
                print()

            # Check for error-related tags
            error_tags = [
                tag for tag in existing_tags if "error" in tag.get("name", "").lower()
            ]
            if error_tags:
                print("🚨 Existing error tags:")
                for tag in error_tags:
                    print(f"  • {tag['name']} (ID: {tag['id']})")
                print()

    except Exception as e:
        print(f"❌ Failed to fetch tags: {e}")
        print()

    # Recommend tags to create
    print("📋 RECOMMENDED ERROR TAGS TO CREATE:")
    print("=" * 40)

    recommended_tags = [
        # Base error detection tags
        "test:error-detection",
        "test:automated-tagging",
        "processing:needs-review",
        # Specific error type tags
        "error:llm",
        "error:confidence",
        "error:pdf",
        "error:metadata",
        "error:validation",
        "error:output",
        # Severity tags
        "error:severity:high",
        "error:severity:critical",
        "error:severity:medium",
    ]

    print("Create these tags in your Paperless web interface:")
    print()
    for i, tag in enumerate(recommended_tags, 1):
        print(f"{i:2d}. {tag}")

    print()
    print("🎯 STEPS TO CREATE TAGS:")
    print("1. Go to https://paperless.lovegroove.io/")
    print("2. Navigate to Settings > Tags")
    print("3. Click 'Create Tag'")
    print("4. Add each tag name from the list above")
    print("5. Optionally assign colors (red for errors, orange for warnings, etc.)")
    print()
    print("💡 TIP: You can copy-paste the tag names directly from above!")

    # Also show what tags would be used with current configuration
    print()
    print("🔧 CURRENT TEST CONFIGURATION WOULD USE:")
    test_config_tags = ["test:error-detection", "test:automated-tagging"]
    for tag in test_config_tags:
        print(f"  • {tag}")

    print()
    print("Once you've created the tags, rerun the integration test!")


if __name__ == "__main__":
    main()
