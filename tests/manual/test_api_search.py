#!/usr/bin/env python3
"""Test direct API search to understand behavior."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import httpx
from bank_statement_separator.config import load_config


def test_api_search():
    """Test direct API search."""
    config = load_config()

    headers = {
        "Authorization": f"Token {config.paperless_token}",
        "Content-Type": "application/json",
    }

    # Test searching for a non-existent tag
    unique_tag = "definitely-does-not-exist-12345"

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{config.paperless_url}/api/tags/",
                headers=headers,
                params={"name": unique_tag},
            )
            response.raise_for_status()

            results = response.json()
            print(f"Search for '{unique_tag}':")
            print(f"  Results count: {results['count']}")
            print(f"  Results: {results['results']}")

            # Also try without name parameter to see all tags
            response2 = client.get(
                f"{config.paperless_url}/api/tags/",
                headers=headers,
                params={"page_size": 5},  # Just get first 5
            )
            response2.raise_for_status()
            all_results = response2.json()
            print("\nFirst 5 existing tags:")
            for tag in all_results["results"]:
                print(f"  ID {tag['id']}: '{tag['name']}'")

    except Exception as e:
        print(f"❌ API search test failed: {e}")


if __name__ == "__main__":
    test_api_search()
