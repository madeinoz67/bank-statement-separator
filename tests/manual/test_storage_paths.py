#!/usr/bin/env python3
"""
Check available storage paths and test document creation with correct path.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def main():
    """Check storage paths and test document creation."""
    print("📁 Checking Available Storage Paths")
    print("=" * 40)

    config = load_config()
    config.paperless_enabled = True

    client = PaperlessClient(config)

    if not client.is_enabled():
        print("❌ Paperless client not enabled")
        return

    try:
        import httpx

        with httpx.Client(timeout=30.0) as http_client:
            # Check available storage paths
            print("📋 Available Storage Paths:")
            try:
                storage_response = http_client.get(
                    f"{config.paperless_url.rstrip('/')}/api/storage_paths/",
                    headers=client.headers,
                )
                storage_response.raise_for_status()

                storage_data = storage_response.json()
                storage_paths = storage_data.get("results", [])

                print(f"✅ Found {len(storage_paths)} storage paths:")
                print()

                test_path_exists = False
                test_path_id = None

                for path in storage_paths:
                    path_id = path.get("id")
                    path_name = path.get("name", "Unknown")
                    path_path = path.get("path", "Unknown")

                    print(f"  • {path_name} (ID: {path_id}) -> {path_path}")

                    if path_name.lower() == "test":
                        test_path_exists = True
                        test_path_id = path_id
                        print(f"    ✅ FOUND 'test' storage path!")

                print()

                if test_path_exists:
                    print(f"✅ 'test' storage path exists with ID: {test_path_id}")
                else:
                    print("⚠️  'test' storage path not found!")
                    print("💡 Available storage paths to use instead:")
                    for path in storage_paths:
                        print(f"  • {path.get('name', 'Unknown')}")

            except Exception as e:
                print(f"❌ Error fetching storage paths: {e}")
                if "403" in str(e):
                    print(
                        "🔒 Access denied - credentials may not have permission to view storage paths"
                    )
                    print("💡 Try creating documents without specifying storage path")

    except Exception as e:
        print(f"❌ Failed to connect: {e}")

    print()
    print("🎯 RECOMMENDATIONS:")
    print("1. If 'test' storage path exists, documents should be created there")
    print("2. If 403 error, create documents without storage_path parameter")
    print("3. Check Paperless web interface: Settings > Storage Paths")


if __name__ == "__main__":
    main()
