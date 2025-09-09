"""Base interface for LLM providers."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BoundaryResult:
    """Result from boundary detection analysis."""

    boundaries: List[Dict[str, Any]]
    confidence: float
    analysis_notes: Optional[str] = None
    provider: Optional[str] = None


@dataclass
class MetadataResult:
    """Result from metadata extraction."""

    metadata: Dict[str, Any]
    confidence: float
    provider: Optional[str] = None


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    pass


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, name: str):
        """
        Initialize LLM provider.

        Args:
            name: Provider name for logging
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and configured.

        Returns:
            bool: True if provider can be used
        """
        pass

    @abstractmethod
    def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
        """
        Analyze text to detect statement boundaries.

        Args:
            text: Document text to analyze
            **kwargs: Additional provider-specific parameters

        Returns:
            BoundaryResult with detected boundaries

        Raises:
            LLMProviderError: If analysis fails
        """
        pass

    @abstractmethod
    def extract_metadata(
        self, text: str, start_page: int, end_page: int, **kwargs
    ) -> MetadataResult:
        """
        Extract metadata from statement text.

        Args:
            text: Statement text
            start_page: Starting page number
            end_page: Ending page number
            **kwargs: Additional provider-specific parameters

        Returns:
            MetadataResult with extracted metadata

        Raises:
            LLMProviderError: If extraction fails
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Get provider information.

        Returns:
            Provider details
        """
        return {
            "name": self.name,
            "available": self.is_available(),
            "type": self.__class__.__name__,
        }
