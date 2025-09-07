#!/usr/bin/env python3
"""Test auto-creation of paperless-ngx entities."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def test_auto_creation():
    """Test auto-creation of new entities."""
    config = load_config()
    client = PaperlessClient(config)

    if not client.is_enabled():
        print("Paperless not enabled")
        return

    print("Testing auto-creation of new entities...")

    try:
        # Test creating new tags that don't exist
        print("\n1. Testing tag creation:")
        new_tags = ["auto-test-tag", "brand-new-tag"]
        tag_ids = client._resolve_tags(new_tags)
        print(f"   Tags {new_tags} -> IDs {tag_ids}")

        # Test creating new correspondent
        print("\n2. Testing correspondent creation:")
        new_correspondent = "Test Auto Bank"
        correspondent_id = client._resolve_correspondent(new_correspondent)
        print(f"   Correspondent '{new_correspondent}' -> ID {correspondent_id}")

        # Test creating new document type
        print("\n3. Testing document type creation:")
        new_doc_type = "Test Auto Statement"
        doc_type_id = client._resolve_document_type(new_doc_type)
        print(f"   Document type '{new_doc_type}' -> ID {doc_type_id}")

        # Test creating new storage path
        print("\n4. Testing storage path creation:")
        new_storage_path = "Test Auto Storage Path"
        storage_path_id = client._resolve_storage_path(new_storage_path)
        print(f"   Storage path '{new_storage_path}' -> ID {storage_path_id}")

        print("\n✅ All auto-creation tests completed successfully!")

    except Exception as e:
        print(f"❌ Auto-creation test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_auto_creation()
