#!/usr/bin/env python3
"""
Simple test script to demonstrate Ollama provider functionality.

Prerequisites:
1. Install and start Ollama server: https://ollama.ai/
2. Pull a compatible model: `ollama pull llama3.2`

Usage:
    python examples/test_ollama.py
"""

import os
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bank_statement_separator.llm import LLMProviderFactory, OllamaProvider
from bank_statement_separator.config import load_config


def test_ollama_availability():
    """Test if Ollama server is running and model is available."""
    print("🦙 Testing Ollama Provider")
    print("=" * 50)

    # Create provider with default settings
    try:
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")

        print("✅ Created Ollama provider:")
        info = provider.get_info()
        for key, value in info.items():
            print(f"   {key}: {value}")

        # Test availability
        print("\n🔍 Testing availability...")
        is_available = provider.is_available()

        if is_available:
            print("✅ Ollama server is running and model is available!")
            return provider
        else:
            print("❌ Ollama server is not available or model not found")
            print("\n💡 To fix this:")
            print("   1. Install Ollama: https://ollama.ai/")
            print("   2. Start Ollama server")
            print("   3. Pull model: ollama pull llama3.2")
            return None

    except Exception as e:
        print(f"❌ Failed to create Ollama provider: {e}")
        return None


def test_boundary_analysis(provider):
    """Test boundary analysis with Ollama."""
    print("\n🔍 Testing Boundary Analysis")
    print("=" * 50)

    # Sample multi-statement document
    sample_text = """
    CHASE BANK STATEMENT
    Account: ****1234
    Statement Period: January 1-31, 2023
    
    [Statement content for Chase account...]
    
    ---
    
    WELLS FARGO STATEMENT  
    Account: ****5678
    Statement Period: January 1-31, 2023
    
    [Statement content for Wells Fargo account...]
    """

    try:
        result = provider.analyze_boundaries(sample_text, total_pages=6)

        print("✅ Boundary analysis completed!")
        print(f"   Confidence: {result.confidence}")
        print(f"   Boundaries found: {len(result.boundaries)}")

        for i, boundary in enumerate(result.boundaries, 1):
            print(
                f"   Statement {i}: Pages {boundary['start_page']}-{boundary['end_page']}"
            )
            if "account_number" in boundary:
                print(f"      Account: {boundary['account_number']}")

        if result.analysis_notes:
            print(f"   Notes: {result.analysis_notes}")

        return True

    except Exception as e:
        print(f"❌ Boundary analysis failed: {e}")
        return False


def test_metadata_extraction(provider):
    """Test metadata extraction with Ollama."""
    print("\n📋 Testing Metadata Extraction")
    print("=" * 50)

    # Sample statement text
    statement_text = """
    CHASE BANK
    Credit Card Statement
    
    John Smith
    123 Main Street
    Anytown, ST 12345
    
    Account Number: ****1234
    Statement Period: January 1, 2023 - January 31, 2023
    
    Previous Balance: $1,234.56
    Payments: -$500.00
    New Purchases: $234.67
    Current Balance: $969.23
    """

    try:
        result = provider.extract_metadata(statement_text, 1, 3)

        print("✅ Metadata extraction completed!")
        print(f"   Confidence: {result.confidence}")
        print("   Extracted metadata:")

        for key, value in result.metadata.items():
            print(f"      {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Metadata extraction failed: {e}")
        return False


def test_factory_integration():
    """Test creating Ollama provider through factory."""
    print("\n🏭 Testing Factory Integration")
    print("=" * 50)

    # Set environment for Ollama
    os.environ["LLM_PROVIDER"] = "ollama"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    os.environ["OLLAMA_MODEL"] = "llama3.2"

    try:
        # Load config and create provider
        config = load_config()
        provider = LLMProviderFactory.create_from_config(config)

        print(f"✅ Factory created provider: {type(provider).__name__}")
        print(f"   Model: {provider.model}")
        print(f"   Base URL: {provider.base_url}")

        return provider

    except Exception as e:
        print(f"❌ Factory creation failed: {e}")
        return None


def main():
    """Run all Ollama tests."""
    print("🧪 Ollama Provider Test Suite")
    print("=" * 50)
    print()

    # Test direct provider creation
    provider = test_ollama_availability()

    if provider:
        # Run functional tests
        test_boundary_analysis(provider)
        test_metadata_extraction(provider)

    # Test factory integration
    factory_provider = test_factory_integration()

    print("\n" + "=" * 50)
    if provider and factory_provider:
        print("🎉 All tests completed successfully!")
        print("\n💡 You can now use Ollama with:")
        print("   LLM_PROVIDER=ollama")
        print("   OLLAMA_BASE_URL=http://localhost:11434")
        print("   OLLAMA_MODEL=llama3.2")
    else:
        print("⚠️  Some tests failed - check Ollama installation")


if __name__ == "__main__":
    main()
