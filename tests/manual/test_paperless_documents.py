#!/usr/bin/env python3
"""
Manual test script to create and verify test documents in paperless-ngx.
This script helps troubleshoot tag assignment and document querying.
"""

from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bank_statement_separator.config import Config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def main():
    print("🔧 Paperless Document Test Script")
    print("=" * 50)

    # Create config
    config = Config(
        openai_api_key="test-key",
        paperless_enabled=True,
        paperless_url="https://paperless.lovegroove.io",
        paperless_token="ca8d0cbc1c54ebb5516bf5e969fce88eace43178",
    )

    client = PaperlessClient(config)

    print("🔌 Testing connection...")
    try:
        client.test_connection()
        print("✅ Connected to paperless-ngx successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    print("\n📄 Querying all documents (first 10)...")
    try:
        result = client.query_documents(page_size=10)
        print(f"📊 Total documents in system: {result['count']}")

        if result["documents"]:
            print("\n📋 Recent documents:")
            for i, doc in enumerate(result["documents"][:5]):
                print(
                    f"  {i + 1}. ID: {doc['id']}, Title: {doc.get('title', 'No title')}"
                )
                # Check if document has test tags
                if "tags" in doc:
                    print(f"     Tags: {doc['tags']}")
                else:
                    print("     Tags: [No tags in response - may need separate query]")

    except Exception as e:
        print(f"❌ Query failed: {e}")

    print("\n🏷️  Querying documents with test:automation tag...")
    try:
        result = client.query_documents_by_tags(["test:automation"])
        print(f"📊 Documents with test:automation tag: {result['count']}")

        if result["count"] > 0:
            print("✅ Found test documents!")
            for doc in result["documents"][:3]:
                print(f"  - {doc['id']}: {doc.get('title', 'No title')}")
        else:
            print("⚠️  No documents found with test:automation tag")

    except Exception as e:
        print(f"❌ Tag query failed: {e}")

    print("\n🔍 Querying all tags to see if test tags exist...")
    try:
        import httpx

        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.get(
                f"{config.paperless_url}/api/tags/",
                headers={"Authorization": f"Token {config.paperless_token}"},
                params={"page_size": 100},
            )
            response.raise_for_status()

            tags_data = response.json()
            test_tags = [
                tag for tag in tags_data["results"] if tag["name"].startswith("test:")
            ]

            print(f"📊 Total tags in system: {tags_data['count']}")
            print(f"🧪 Test tags found: {len(test_tags)}")

            if test_tags:
                print("✅ Test tags exist:")
                for tag in test_tags:
                    print(f"  - {tag['name']} (ID: {tag['id']})")
            else:
                print("⚠️  No test tags found - tags may not be applied correctly")

    except Exception as e:
        print(f"❌ Tag listing failed: {e}")


if __name__ == "__main__":
    main()
