#!/usr/bin/env python3
"""
Verify final results: Documents in 'test' storage path with error tags applied.
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
    """Verify final results of error tagging in test storage path."""
    print("🎯 FINAL VERIFICATION RESULTS")
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
            # Get today's FINAL test documents
            today = datetime.now().strftime("%Y-%m-%d")

            response = http_client.get(
                f"{config.paperless_url.rstrip('/')}/api/documents/?title__icontains=FINAL&created__date__gte={today}&ordering=-created&page_size=10",
                headers=client.headers,
            )
            response.raise_for_status()

            docs_data = response.json()
            documents = docs_data.get("results", [])

            print(f"📋 Documents created today with 'FINAL' in title:")
            print()

            if not documents:
                print("❌ No FINAL test documents found for today")
                return

            success_count = 0

            for doc in documents:
                doc_id = doc.get("id")
                title = doc.get("title", "Unknown")
                created = doc.get("created", "Unknown")
                storage_path = doc.get("storage_path")

                # Get storage path name
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
                    except:
                        storage_path_name = f"ID:{storage_path}"

                # Get document tags
                try:
                    doc_response = http_client.get(
                        f"{config.paperless_url.rstrip('/')}/api/documents/{doc_id}/",
                        headers=client.headers,
                    )
                    if doc_response.status_code == 200:
                        doc_details = doc_response.json()
                        tag_ids = doc_details.get("tags", [])

                        # Get tag names
                        tag_names = []
                        for tag_id in tag_ids:
                            try:
                                tag_response = http_client.get(
                                    f"{config.paperless_url.rstrip('/')}/api/tags/{tag_id}/",
                                    headers=client.headers,
                                )
                                if tag_response.status_code == 200:
                                    tag_data = tag_response.json()
                                    tag_names.append(
                                        tag_data.get("name", f"ID:{tag_id}")
                                    )
                            except:
                                tag_names.append(f"ID:{tag_id}")

                        print(f"📄 Document {doc_id}: {title}")
                        print(f"   • Created: {created[:10]}")
                        print(f"   • Storage Path: {storage_path_name}")
                        print(f"   • Tags Applied: {len(tag_names)}")

                        if tag_names:
                            print(f"   • Tag Names:")
                            for tag in sorted(tag_names):
                                print(f"     - {tag}")

                        # Check if in test storage and has error tags
                        has_test_storage = storage_path_name.lower() == "test"
                        has_error_tags = any(
                            "error" in tag.lower() for tag in tag_names
                        )

                        if has_test_storage and has_error_tags:
                            success_count += 1
                            print(f"   ✅ SUCCESS: In 'test' storage with error tags!")
                        elif has_test_storage:
                            print(f"   ⚠️  In 'test' storage but no error tags")
                        elif has_error_tags:
                            print(f"   ⚠️  Has error tags but wrong storage path")
                        else:
                            print(f"   ❌ Missing both test storage and error tags")

                        print()

                except Exception as e:
                    print(f"   ❌ Error fetching document details: {e}")
                    print()

            print("=" * 50)
            print(f"🎉 FINAL RESULTS SUMMARY:")
            print(f"  • Total documents found: {len(documents)}")
            print(f"  • Successfully configured: {success_count}")
            print(f"  • Success rate: {success_count / len(documents) * 100:.1f}%")

            if success_count == len(documents):
                print()
                print("🚀 COMPLETE SUCCESS!")
                print(
                    "✅ All documents are in 'test' storage path with error tags applied!"
                )
                print("✅ Error detection and tagging system is fully operational!")
            elif success_count > 0:
                print()
                print(
                    f"🎯 Partial success: {success_count}/{len(documents)} documents configured correctly"
                )
            else:
                print()
                print("⚠️  No documents were configured correctly")

    except Exception as e:
        print(f"❌ Failed to verify results: {e}")


if __name__ == "__main__":
    main()
