#!/usr/bin/env python3
"""
Check recent documents and their storage paths.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def main():
    """Check recent documents and storage paths."""
    print("🔍 Checking Recent Documents and Storage Paths")
    print("=" * 50)

    config = load_config()
    config.paperless_enabled = True

    client = PaperlessClient(config)

    if not client.is_enabled():
        print("❌ Paperless client not enabled")
        return

    try:
        import httpx

        with httpx.Client(timeout=30.0) as http_client:
            # Get recent documents created today
            today = datetime.now().strftime("%Y-%m-%d")

            response = http_client.get(
                f"{config.paperless_url.rstrip('/')}/api/documents/?created__date__gte={today}&ordering=-created&page_size=10",
                headers=client.headers,
            )
            response.raise_for_status()

            docs_data = response.json()
            documents = docs_data.get("results", [])

            print(f"📋 Documents created today ({today}):")
            print()

            if not documents:
                print("❌ No documents created today")
                return

            for doc in documents:
                doc_id = doc.get("id")
                title = doc.get("title", "Unknown")
                created = doc.get("created", "Unknown")
                storage_path = doc.get("storage_path")
                tags = doc.get("tags", [])

                # Get storage path name if it's an ID
                storage_path_name = "Default"
                if storage_path:
                    try:
                        storage_response = http_client.get(
                            f"{config.paperless_url.rstrip('/')}/api/storage_paths/{storage_path}/",
                            headers=client.headers,
                        )
                        if storage_response.status_code == 200:
                            storage_data = storage_response.json()
                            storage_path_name = storage_data.get(
                                "name", f"ID:{storage_path}"
                            )
                    except (KeyError, TypeError, AttributeError):
                        storage_path_name = f"ID:{storage_path}"

                print(f"📄 Document {doc_id}: {title}")
                print(f"   • Created: {created}")
                print(f"   • Storage Path: {storage_path_name}")
                print(
                    f"   • Tags: {[tag.get('name', 'Unknown') for tag in tags] if tags else 'None'}"
                )
                print()

            # Also check for test documents with specific filenames
            print("🔍 Looking for test documents with error detection filenames...")

            response = http_client.get(
                f"{config.paperless_url.rstrip('/')}/api/documents/?title__icontains=test_statement_error_detection&ordering=-created&page_size=10",
                headers=client.headers,
            )
            response.raise_for_status()

            test_docs_data = response.json()
            test_documents = test_docs_data.get("results", [])

            if test_documents:
                print(f"Found {len(test_documents)} test error detection documents:")
                print()

                for doc in test_documents:
                    doc_id = doc.get("id")
                    title = doc.get("title", "Unknown")
                    created = doc.get("created", "Unknown")
                    storage_path = doc.get("storage_path")

                    storage_path_name = "Default"
                    if storage_path:
                        try:
                            storage_response = http_client.get(
                                f"{config.paperless_url.rstrip('/')}/api/storage_paths/{storage_path}/",
                                headers=client.headers,
                            )
                            if storage_response.status_code == 200:
                                storage_data = storage_response.json()
                                storage_path_name = storage_data.get(
                                    "name", f"ID:{storage_path}"
                                )
                        except (KeyError, TypeError, AttributeError):
                            storage_path_name = f"ID:{storage_path}"

                    print(f"📄 Document {doc_id}: {title}")
                    print(f"   • Created: {created}")
                    print(f"   • Storage Path: {storage_path_name}")
                    print()
            else:
                print("❌ No test error detection documents found")

            # Check available storage paths
            print("📁 Available Storage Paths:")
            try:
                storage_response = http_client.get(
                    f"{config.paperless_url.rstrip('/')}/api/storage_paths/",
                    headers=client.headers,
                )
                if storage_response.status_code == 200:
                    storage_data = storage_response.json()
                    storage_paths = storage_data.get("results", [])

                    for path in storage_paths:
                        path_id = path.get("id")
                        path_name = path.get("name", "Unknown")
                        path_path = path.get("path", "Unknown")
                        print(f"  • {path_name} (ID: {path_id}) -> {path_path}")
                else:
                    print(
                        f"  ❌ Could not fetch storage paths (Status: {storage_response.status_code})"
                    )
            except Exception as e:
                print(f"  ❌ Error fetching storage paths: {e}")

    except Exception as e:
        print(f"❌ Failed to fetch documents: {e}")


if __name__ == "__main__":
    main()
