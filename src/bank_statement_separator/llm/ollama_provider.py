"""Ollama LLM provider implementation for local AI processing."""

import json
import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from ..utils.hallucination_detector import HallucinationDetector
from .base import BoundaryResult, LLMProvider, LLMProviderError, MetadataResult

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM processing."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs,
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL
            model: Model name to use
            temperature: Model temperature (0-1)
            max_tokens: Maximum tokens per response
            **kwargs: Additional parameters
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.hallucination_detector = HallucinationDetector()

        try:
            # Initialize ChatOllama instance
            self.llm = ChatOllama(
                base_url=base_url,
                model=model,
                temperature=temperature,
                num_predict=max_tokens,  # Ollama uses num_predict for max_tokens
                **kwargs,
            )
            logger.info(f"Initialized Ollama provider with model {model} at {base_url}")

        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            raise LLMProviderError(f"Ollama initialization failed: {e}")

    def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
        """Analyze document text to detect statement boundaries.

        Args:
            text: Document text to analyze
            **kwargs: Additional parameters (total_pages, etc.)

        Returns:
            BoundaryResult with detected boundaries

        Raises:
            LLMProviderError: If analysis fails
        """
        try:
            prompt = self._create_boundary_prompt(text, **kwargs)
            logger.debug(f"Ollama analyzing boundaries for {len(text)} characters")

            # Create message and get response
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])

            # Parse the response
            result = self._parse_boundary_response(response.content)

            # Validate for hallucinations
            total_pages = kwargs.get("total_pages", len(text.split("\n---\n")))
            hallucination_alerts = (
                self.hallucination_detector.validate_boundary_response(
                    result.boundaries, total_pages, text
                )
            )

            # Log hallucination alerts
            self.hallucination_detector.log_hallucination_alerts(
                hallucination_alerts, "(Ollama boundary analysis)"
            )

            # Check if response should be rejected due to hallucinations
            if self.hallucination_detector.should_reject_response(hallucination_alerts):
                logger.error(
                    "🚨 CRITICAL HALLUCINATION: Rejecting Ollama boundary response due to severe hallucinations"
                )
                raise LLMProviderError(
                    "Boundary analysis rejected due to detected hallucinations - falling back to pattern matching"
                )

            logger.info(
                f"Ollama detected {len(result.boundaries)} boundaries (validated, {len(hallucination_alerts)} alerts)"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Ollama boundary response parsing failed: {e}")
            raise LLMProviderError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Ollama boundary analysis failed: {e}")
            raise LLMProviderError(f"Boundary analysis failed: {e}")

    def extract_metadata(
        self, text: str, start_page: int, end_page: int, **kwargs
    ) -> MetadataResult:
        """Extract metadata from a statement section.

        Args:
            text: Statement text to analyze
            start_page: Starting page number
            end_page: Ending page number
            **kwargs: Additional parameters

        Returns:
            MetadataResult with extracted metadata

        Raises:
            LLMProviderError: If extraction fails
        """
        try:
            prompt = self._create_metadata_prompt(text, start_page, end_page, **kwargs)
            logger.debug(
                f"Ollama extracting metadata from pages {start_page}-{end_page}"
            )

            # Create message and get response
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])

            # Parse the response
            result = self._parse_metadata_response(response.content)

            # Validate for hallucinations
            hallucination_alerts = (
                self.hallucination_detector.validate_metadata_response(
                    result.metadata, text, (start_page, end_page)
                )
            )

            # Log hallucination alerts
            self.hallucination_detector.log_hallucination_alerts(
                hallucination_alerts,
                f"(Ollama metadata extraction pages {start_page}-{end_page})",
            )

            # Check if response should be rejected due to hallucinations
            if self.hallucination_detector.should_reject_response(hallucination_alerts):
                logger.error(
                    "🚨 CRITICAL HALLUCINATION: Rejecting Ollama metadata response due to severe hallucinations"
                )
                raise LLMProviderError(
                    "Metadata extraction rejected due to detected hallucinations - using fallback"
                )

            logger.info(
                f"Ollama extracted metadata with confidence {result.confidence} (validated, {len(hallucination_alerts)} alerts)"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Ollama metadata response parsing failed: {e}")
            raise LLMProviderError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Ollama metadata extraction failed: {e}")
            raise LLMProviderError(f"Metadata extraction failed: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Get provider information and status."""
        return {
            "name": "ollama",
            "type": "OllamaProvider",
            "model": self.model,
            "base_url": self.base_url,
            "available": self.is_available(),
            "features": [
                "boundary_analysis",
                "metadata_extraction",
                "local_processing",
            ],
            "version": "1.0.0",
            "privacy": "high",  # Local processing
            "cost": "free",  # No API costs
        }

    def is_available(self) -> bool:
        """Check if Ollama provider is available and configured.

        Returns:
            True if provider is available, False otherwise
        """
        try:
            # Test basic connectivity with a simple prompt
            test_message = HumanMessage(content="Hello, respond with just 'OK'")
            response = self.llm.invoke([test_message])

            # Check if we got a reasonable response
            if response and hasattr(response, "content"):
                logger.debug(
                    f"Ollama availability check passed: {response.content[:50]}..."
                )
                return True
            else:
                logger.warning("Ollama availability check failed: no valid response")
                return False

        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False

    def _create_boundary_prompt(self, text: str, **kwargs) -> str:
        """Create prompt for boundary analysis."""
        total_pages = kwargs.get("total_pages", len(text.split("\n---\n")))

        return f"""You are a bank statement analyzer. Analyze this document and identify individual bank statement boundaries.

DOCUMENT TEXT ({total_pages} pages):
{text}

TASK: Identify where each separate bank statement begins and ends.

Look for these boundary indicators:
- Bank headers and letterheads (e.g., "NAB", "Westpac", "Commonwealth Bank")
- Different account numbers (even if similar, e.g., 084234123456 vs 084234123457)
- New statement periods (From/To dates - different date ranges)
- Page numbering resets (Page 1 of X starting over)
- Changes in customer names or addresses
- Different bank branding/formatting
- Account type changes (e.g., "iSaver" vs "Visa Credit")

CRITICAL INSTRUCTIONS:
- Each statement must be complete (no overlapping pages)
- Account for ALL {total_pages} pages in the document
- Similar account numbers often indicate separate statements
- Look carefully at statement dates - different periods = different statements
- If you see "Page 1 of X" multiple times, those are likely separate statements

RESPONSE FORMAT: Return ONLY a valid JSON object with this structure:
{{
    "total_statements": <number>,
    "boundaries": [
        {{
            "start_page": <number>,
            "end_page": <number>,
            "account_number": "<account_identifier_if_found>"
        }}
    ],
    "confidence": <float_0_to_1>
}}

Be precise with page numbers. Each statement should be complete and not overlap."""

    def _create_metadata_prompt(
        self, text: str, start_page: int, end_page: int, **kwargs
    ) -> str:
        """Create prompt for metadata extraction."""
        return f"""You are a bank statement analyzer. Extract key metadata from this bank statement section.

STATEMENT TEXT (pages {start_page}-{end_page}):
{text}

TASK: Extract the following information from this bank statement:

RESPONSE FORMAT: Return ONLY a valid JSON object with this structure:
{{
    "bank_name": "<full_bank_name>",
    "account_number": "<account_number_or_card_number>",
    "account_type": "<account_type_eg_checking_savings_credit>",
    "statement_period": "<period_eg_jan_2023_or_2023_01_01_to_2023_01_31>",
    "customer_name": "<customer_name_if_found>",
    "confidence": <float_0_to_1>
}}

Look for:
- Bank name in headers, footers, or letterhead
- Account numbers (may be partially masked like ****1234)
- Account types (checking, savings, credit card, etc.)
- Statement date ranges
- Customer/account holder names

If information is not found, use empty string. Set confidence based on how much information you found."""

    def _parse_boundary_response(self, response_content: str) -> BoundaryResult:
        """Parse boundary analysis response from Ollama.

        Args:
            response_content: Raw response content from Ollama

        Returns:
            BoundaryResult object

        Raises:
            LLMProviderError: If parsing fails
        """
        try:
            # Clean the response content (remove any markdown formatting and text)
            cleaned_content = response_content.strip()

            # Remove common prefixes that models add
            prefixes_to_remove = [
                "Here is the JSON response:",
                "Here's the JSON response:",
                "Here is the response:",
                "Here's the response:",
                "Here is the JSON:",
                "Here's the JSON:",
                "Response:",
                "JSON:",
            ]

            for prefix in prefixes_to_remove:
                if cleaned_content.startswith(prefix):
                    cleaned_content = cleaned_content[len(prefix) :].strip()
                    break

            # Handle markdown code blocks
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]

            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()

            # Find JSON object boundaries (handle cases where model adds extra text)
            json_start = cleaned_content.find("{")
            json_end = cleaned_content.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                cleaned_content = cleaned_content[json_start:json_end]

            # Fix common JSON formatting issues from Ollama models
            # Fix unquoted values like ****1234 -> "****1234"
            import re

            # Pattern to match unquoted account numbers like ****1234 or similar patterns
            unquoted_pattern = r'("account_number":\s*)([*\d\w]+)([,\s\}])'
            cleaned_content = re.sub(unquoted_pattern, r'\1"\2"\3', cleaned_content)

            # Parse JSON
            data = json.loads(cleaned_content)

            # Validate required fields
            if "boundaries" not in data:
                raise ValueError("Missing 'boundaries' field in response")

            boundaries = data["boundaries"]
            if not isinstance(boundaries, list):
                raise ValueError("'boundaries' must be a list")

            # Validate each boundary
            for i, boundary in enumerate(boundaries):
                if not isinstance(boundary, dict):
                    raise ValueError(f"Boundary {i} must be a dictionary")
                if "start_page" not in boundary or "end_page" not in boundary:
                    raise ValueError(f"Boundary {i} missing start_page or end_page")

            return BoundaryResult(
                boundaries=boundaries,
                confidence=data.get("confidence", 0.8),
                analysis_notes=f"Ollama detected {len(boundaries)} statement boundaries",
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Ollama boundary response: {e}")
            logger.error(f"Raw response: {response_content[:500]}...")
            raise LLMProviderError(f"Invalid boundary response format: {e}")

    def _parse_metadata_response(self, response_content: str) -> MetadataResult:
        """Parse metadata extraction response from Ollama.

        Args:
            response_content: Raw response content from Ollama

        Returns:
            MetadataResult object

        Raises:
            LLMProviderError: If parsing fails
        """
        try:
            # Clean the response content (remove any markdown formatting and text)
            cleaned_content = response_content.strip()

            # Remove common prefixes that models add
            prefixes_to_remove = [
                "Here is the JSON response:",
                "Here's the JSON response:",
                "Here is the response:",
                "Here's the response:",
                "Here is the JSON:",
                "Here's the JSON:",
                "Response:",
                "JSON:",
            ]

            for prefix in prefixes_to_remove:
                if cleaned_content.startswith(prefix):
                    cleaned_content = cleaned_content[len(prefix) :].strip()
                    break

            # Handle markdown code blocks
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            elif cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]

            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()

            # Find JSON object boundaries (handle cases where model adds extra text)
            json_start = cleaned_content.find("{")
            json_end = cleaned_content.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                cleaned_content = cleaned_content[json_start:json_end]

            # Parse JSON
            data = json.loads(cleaned_content)

            # Extract metadata with defaults
            metadata = {
                "bank_name": data.get("bank_name", "Unknown"),
                "account_number": data.get("account_number", ""),
                "account_type": data.get("account_type", ""),
                "statement_period": data.get("statement_period", ""),
                "customer_name": data.get("customer_name", ""),
            }

            # Clean up empty fields
            metadata = {k: v for k, v in metadata.items() if v}

            return MetadataResult(
                metadata=metadata, confidence=data.get("confidence", 0.7)
            )

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Ollama metadata response: {e}")
            logger.error(f"Raw response: {response_content[:500]}...")
            raise LLMProviderError(f"Invalid metadata response format: {e}")
