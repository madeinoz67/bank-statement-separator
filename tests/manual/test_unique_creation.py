#!/usr/bin/env python3
"""Test creation of truly unique paperless-ngx entities."""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def test_unique_creation():
    """Test creation of unique entities with UUID suffixes."""
    config = load_config()
    client = PaperlessClient(config)

    if not client.is_enabled():
        print("Paperless not enabled")
        return

    # Generate unique identifiers
    unique_id = str(uuid.uuid4())[:8]
    print(f"Testing auto-creation with unique ID: {unique_id}")

    try:
        # Test creating truly unique tags
        print("\n1. Testing unique tag creation:")
        unique_tags = [f"test-tag-{unique_id}", f"another-tag-{unique_id}"]
        tag_ids = client._resolve_tags(unique_tags)
        print(f"   Tags {unique_tags} -> IDs {tag_ids}")

        # Test creating unique correspondent
        print("\n2. Testing unique correspondent creation:")
        unique_correspondent = f"Test Bank {unique_id}"
        correspondent_id = client._resolve_correspondent(unique_correspondent)
        print(f"   Correspondent '{unique_correspondent}' -> ID {correspondent_id}")

        # Test creating unique document type
        print("\n3. Testing unique document type creation:")
        unique_doc_type = f"Test Statement {unique_id}"
        doc_type_id = client._resolve_document_type(unique_doc_type)
        print(f"   Document type '{unique_doc_type}' -> ID {doc_type_id}")

        # Test creating unique storage path
        print("\n4. Testing unique storage path creation:")
        unique_storage = f"Test Storage {unique_id}"
        storage_id = client._resolve_storage_path(unique_storage)
        print(f"   Storage path '{unique_storage}' -> ID {storage_id}")

        print(
            f"\n✅ All unique entities created successfully with ID suffix: {unique_id}"
        )

    except Exception as e:
        print(f"❌ Unique creation test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_unique_creation()
