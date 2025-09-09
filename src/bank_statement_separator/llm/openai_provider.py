"""OpenAI LLM provider implementation."""

import logging
import os
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from openai import APIError, RateLimitError
from pydantic import BaseModel

from ..utils.hallucination_detector import HallucinationDetector
from ..utils.rate_limiter import (
    BackoffStrategy,
    RateLimitConfig,
    RateLimiter,
    load_rate_limit_config_from_env,
)
from .base import BoundaryResult, LLMProvider, LLMProviderError, MetadataResult

logger = logging.getLogger(__name__)


class StatementBoundaries(BaseModel):
    """Pydantic model for statement boundary detection."""

    total_statements: int
    boundaries: List[Dict[str, Any]]


class StatementMetadata(BaseModel):
    """Pydantic model for statement metadata."""

    bank_name: str
    account_number: Optional[str] = None
    account_type: Optional[str] = None
    statement_period: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    confidence: float = 0.8


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider using ChatGPT models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_retries: int = 2,
        rate_limit_config: Optional[RateLimitConfig] = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            model: Model name to use
            temperature: Sampling temperature
            max_retries: Maximum retry attempts
            rate_limit_config: Rate limiting configuration
        """
        super().__init__("openai")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries

        # Initialize rate limiting
        self.rate_limit_config = rate_limit_config or load_rate_limit_config_from_env()
        self.rate_limiter = RateLimiter(self.rate_limit_config)

        self.hallucination_detector = HallucinationDetector()

        if self.api_key:
            self.llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
                max_retries=0,  # Disable LangChain retries, use our own
            )
        else:
            self.llm = None

    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return bool(self.api_key and self.llm)

    def _execute_with_rate_limiting(self, func, *args, **kwargs):
        """
        Execute API call with rate limiting and backoff.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the function call

        Raises:
            LLMProviderError: On rate limit or API errors
        """
        try:
            # Acquire rate limit permission
            if not self.rate_limiter.acquire():
                logger.warning("Rate limit exceeded, implementing backoff")
                raise LLMProviderError(
                    f"OpenAI rate limit exceeded. "
                    f"Limit: {self.rate_limit_config.requests_per_minute}/min"
                )

            # Execute with backoff strategy
            return BackoffStrategy.execute_with_backoff(
                func,
                self.max_retries,
                self.rate_limit_config.backoff_min,
                *args,
                **kwargs,
            )

        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit error: {e}")
            raise LLMProviderError(
                f"OpenAI rate limit exceeded after {self.max_retries} retries. "
                f"Limit: {self.rate_limit_config.requests_per_minute}/min"
            )
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMProviderError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in rate-limited execution: {e}")
            raise

    def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
        """
        Analyze text to detect statement boundaries using OpenAI.

        Args:
            text: Document text to analyze
            **kwargs: Additional parameters

        Returns:
            BoundaryResult with detected boundaries

        Raises:
            LLMProviderError: If analysis fails
        """
        if not self.is_available():
            raise LLMProviderError("OpenAI provider not available - missing API key")

        try:
            # Create parser
            parser = PydanticOutputParser(pydantic_object=StatementBoundaries)

            # Create messages
            system_msg = SystemMessage(
                content="""You are a financial document analyzer specializing in bank statements.
Analyze the provided text and identify individual bank statement boundaries.

Each statement typically:
1. Starts with bank header/logo information
2. Contains account holder details
3. Has a statement period or date range
4. Includes transaction listings
5. Ends with balance summaries

Identify where each complete statement begins and ends."""
            )

            # Get total pages from kwargs or estimate from text
            total_pages = kwargs.get("total_pages", text.count("\n---\n") + 1)

            # Use more text but still within limits - prioritize beginning and end sections
            text_sample = text[:12000]  # Increased limit
            if len(text) > 12000:
                text_sample += (
                    "\n\n... [MIDDLE CONTENT TRUNCATED] ...\n\n" + text[-4000:]
                )

            human_msg = HumanMessage(
                content=f"""Analyze this bank statement document ({total_pages} pages) and identify all individual statement boundaries.

DOCUMENT TEXT:
{text_sample}

TASK: Find where each separate bank statement begins and ends.

Look for these boundary indicators:
- Bank headers and letterheads
- Different account numbers
- New statement periods (From/To dates)
- Page numbering resets (Page 1 of X)
- Changes in customer names or addresses
- Different bank branding/formatting

CRITICAL:
- Each statement must be complete (no overlapping pages)
- Account for all {total_pages} pages in the document
- If similar account numbers, look carefully at dates and statement periods

{parser.get_format_instructions()}

Provide precise page boundaries for each detected statement."""
            )

            # Get response with rate limiting
            response = self._execute_with_rate_limiting(
                self.llm.invoke, [system_msg, human_msg]
            )

            # Parse response
            try:
                result = parser.parse(response.content)

                # Validate for hallucinations
                total_pages = kwargs.get(
                    "total_pages", text[:12000].count("\n---\n") + 1
                )
                hallucination_alerts = (
                    self.hallucination_detector.validate_boundary_response(
                        result.boundaries,
                        total_pages,
                        text[:12000],  # Use same text sample as prompt
                    )
                )

                # Log hallucination alerts
                self.hallucination_detector.log_hallucination_alerts(
                    hallucination_alerts, "(OpenAI boundary analysis)"
                )

                # Check if response should be rejected due to hallucinations
                if self.hallucination_detector.should_reject_response(
                    hallucination_alerts
                ):
                    self.logger.error(
                        "🚨 CRITICAL HALLUCINATION: Rejecting OpenAI boundary response due to severe hallucinations"
                    )
                    raise LLMProviderError(
                        "Boundary analysis rejected due to detected hallucinations - falling back to pattern matching"
                    )

                return BoundaryResult(
                    boundaries=result.boundaries,
                    confidence=0.9,
                    analysis_notes=f"OpenAI {self.model} detected {result.total_statements} statements (validated, {len(hallucination_alerts)} alerts)",
                    provider="openai",
                )
            except Exception as parse_error:
                self.logger.warning(f"Failed to parse OpenAI response: {parse_error}")
                # Return basic result
                return BoundaryResult(
                    boundaries=[{"start_page": 1, "end_page": -1}],
                    confidence=0.5,
                    analysis_notes="Failed to parse structured response, assuming single statement",
                    provider="openai",
                )

        except Exception as e:
            logger.error(f"OpenAI boundary detection failed: {e}")
            raise LLMProviderError(f"OpenAI analysis failed: {str(e)}")

    def extract_metadata(
        self, text: str, start_page: int, end_page: int, **kwargs
    ) -> MetadataResult:
        """
        Extract metadata from statement text using OpenAI.

        Args:
            text: Statement text
            start_page: Starting page number
            end_page: Ending page number
            **kwargs: Additional parameters

        Returns:
            MetadataResult with extracted metadata

        Raises:
            LLMProviderError: If extraction fails
        """
        if not self.is_available():
            raise LLMProviderError("OpenAI provider not available - missing API key")

        try:
            # Create parser
            parser = PydanticOutputParser(pydantic_object=StatementMetadata)

            # Create messages
            system_msg = SystemMessage(
                content="""You are a financial document analyzer.
Extract key metadata from the bank statement text provided.

Focus on identifying:
1. Bank name and institution
2. Account number (full or partial)
3. Account type (Checking, Savings, Credit Card, etc.)
4. Statement period or date range
5. Any other relevant identifiers"""
            )

            # Smart text sampling to ensure account information is included
            text_sample = self._prepare_metadata_text_sample(text)

            human_msg = HumanMessage(
                content=f"""Extract metadata from this bank statement section (pages {start_page}-{end_page}):

{text_sample}

{parser.get_format_instructions()}

Provide your confidence level (0.0-1.0) based on how clearly the information is present."""
            )

            # Get response with rate limiting
            response = self._execute_with_rate_limiting(
                self.llm.invoke, [system_msg, human_msg]
            )

            # Parse response
            try:
                result = parser.parse(response.content)

                # Debug logging for failed extractions
                if not result.account_number and not result.account_type:
                    logger.warning(
                        f"LLM metadata extraction failed to find account info for pages {start_page}-{end_page}"
                    )
                    logger.warning(f"LLM Response content: {response.content}")
                    logger.warning(f"Text sample length: {len(text_sample)} chars")
                    logger.warning(f"Text sample preview: {text_sample[:500]}...")

                metadata = {
                    "bank_name": result.bank_name,
                    "account_number": result.account_number,
                    "account_type": result.account_type,
                    "statement_period": result.statement_period,
                    "start_date": result.start_date,
                    "end_date": result.end_date,
                    "start_page": start_page,
                    "end_page": end_page,
                    "confidence": result.confidence,
                }

                return MetadataResult(
                    metadata=metadata, confidence=result.confidence, provider="openai"
                )
            except Exception as parse_error:
                logger.warning(f"Failed to parse metadata response: {parse_error}")
                logger.debug(f"Raw LLM response: {response.content}")
                # Return minimal metadata
                return MetadataResult(
                    metadata={
                        "start_page": start_page,
                        "end_page": end_page,
                        "confidence": 0.3,
                    },
                    confidence=0.3,
                    provider="openai",
                )

        except Exception as e:
            logger.error(f"OpenAI metadata extraction failed: {e}")
            raise LLMProviderError(f"OpenAI extraction failed: {str(e)}")

    def _prepare_metadata_text_sample(self, text: str) -> str:
        """
        Prepare text sample for metadata extraction, ensuring account information is included.

        Args:
            text: Full statement text

        Returns:
            Optimized text sample for LLM processing
        """
        import re

        # If text is short enough, use it all
        if len(text) <= 6000:
            return text

        # Look for account number patterns in the text
        account_patterns = [
            r"(?i)account\s+(?:number|no\.?|#)?\s*:?\s*(\d[\d\s\-]{8,})",
            r"(?i)card\s+(?:number|no\.?)\s*:?\s*(\d[\d\s\-]{12,})",
            r"(?i)account\s*number\s+(\d[\d\s\-]{8,})",
            r"\b\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\b",  # 4-4-4-4 format
            r"\b\d{10,16}\b",  # 10-16 consecutive digits
        ]

        # Find all account number matches with their positions
        account_matches = []
        for pattern in account_patterns:
            for match in re.finditer(pattern, text):
                account_matches.append((match.start(), match.end(), match.group(0)))

        # Sort by position
        account_matches.sort(key=lambda x: x[0])

        # If we found account numbers, ensure they're included in the sample
        if account_matches:
            # Take first 3000 chars, then add sections around account numbers, then last 2000 chars
            sample_parts = []

            # Always include the beginning
            sample_parts.append(text[:3000])

            # Add sections around account numbers (up to 1000 chars each)
            added_positions = set()
            for start_pos, end_pos, match_text in account_matches[
                :3
            ]:  # Limit to 3 account sections
                # Find a good window around this account number
                window_start = max(0, start_pos - 500)
                window_end = min(len(text), end_pos + 500)

                # Avoid overlapping with already added content
                if not any(pos <= window_end for pos in added_positions):
                    sample_parts.append(
                        f"\n[... ACCOUNT INFO SECTION ...]\n{text[window_start:window_end]}"
                    )
                    added_positions.add(window_start)

            # Add end section if there's room
            if len("".join(sample_parts)) < 5000:
                remaining_space = 6000 - len("".join(sample_parts))
                if remaining_space > 1000:
                    end_start = max(0, len(text) - remaining_space)
                    sample_parts.append(f"\n[... END SECTION ...]\n{text[end_start:]}")

            final_sample = "".join(sample_parts)
            if len(final_sample) > 6000:
                final_sample = final_sample[:6000] + "\n[... TEXT TRUNCATED ...]"

            return final_sample

        # Fallback: if no account numbers found, use standard truncation
        if len(text) > 6000:
            return (
                text[:4000]
                + "\n\n[... MIDDLE CONTENT TRUNCATED ...]\n\n"
                + text[-2000:]
            )

        return text
