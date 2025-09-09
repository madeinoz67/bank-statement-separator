"""Factory for creating LLM providers."""

import logging
from typing import Any, Dict, Optional

from .base import LLMProvider, LLMProviderError
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for creating and managing LLM providers."""

    # Registry of available providers
    _providers = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register a new provider type.

        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered LLM provider: {name}")

    @classmethod
    def create_provider(
        cls, provider_type: str, config: Optional[Dict[str, Any]] = None
    ) -> LLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_type: Type of provider ("openai", "ollama", etc.)
            config: Provider-specific configuration

        Returns:
            LLMProvider instance

        Raises:
            LLMProviderError: If provider type is unknown or creation fails
        """
        if provider_type not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise LLMProviderError(
                f"Unknown provider type: {provider_type}. Available: {available}"
            )

        provider_class = cls._providers[provider_type]
        config = config or {}

        try:
            provider = provider_class(**config)
            logger.info(f"Created {provider_type} provider")
            return provider
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {e}")
            raise LLMProviderError(
                f"Failed to create {provider_type} provider: {str(e)}"
            )

    @classmethod
    def create_from_config(cls, app_config: Any) -> LLMProvider:
        """
        Create provider from application configuration.

        Args:
            app_config: Application configuration object

        Returns:
            LLMProvider instance

        Raises:
            LLMProviderError: If creation fails
        """
        # Determine provider type
        provider_type = getattr(app_config, "llm_provider", "openai")

        # Build provider config based on type
        if provider_type == "openai":
            provider_config = {
                "api_key": getattr(app_config, "openai_api_key", None),
                "model": getattr(app_config, "openai_model", "gpt-4o-mini"),
                "temperature": getattr(app_config, "llm_temperature", 0.1),
            }
        elif provider_type == "ollama":
            provider_config = {
                "base_url": getattr(
                    app_config, "ollama_base_url", "http://localhost:11434"
                ),
                "model": getattr(app_config, "ollama_model", "llama3.2"),
                "temperature": getattr(app_config, "llm_temperature", 0.1),
                "max_tokens": getattr(app_config, "llm_max_tokens", 4000),
            }
        else:
            provider_config = {}

        return cls.create_provider(provider_type, provider_config)

    @classmethod
    def get_available_providers(cls) -> Dict[str, bool]:
        """
        Get status of all registered providers.

        Returns:
            Dict mapping provider names to availability status
        """
        status = {}
        for name in cls._providers:
            try:
                provider = cls.create_provider(name)
                status[name] = provider.is_available()
            except Exception:
                status[name] = False
        return status
