#!/usr/bin/env python3
"""Test creation with verbose logging."""

import sys
import uuid
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def test_with_logging():
    """Test with debug logging enabled."""
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)

    config = load_config()
    client = PaperlessClient(config)

    unique_id = str(uuid.uuid4())[:8]
    print(f"Testing with unique ID: {unique_id}")

    try:
        print("\nTesting tag creation with debug logging:")
        unique_tag = f"debug-tag-{unique_id}"
        tag_id = client._resolve_tags([unique_tag])
        print(f"Final result: Tag '{unique_tag}' -> ID {tag_id}")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_with_logging()
