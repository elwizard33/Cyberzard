"""Model selector for unified LLM instantiation.

This module provides the ModelSelector class that handles:
- Provider detection (installed packages and API keys)
- Provider validation
- Model creation using LangChain's init_chat_model

This is the single source of truth for LLM instantiation across Cyberzard.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .registry import PROVIDERS, ProviderInfo, get_provider, list_providers


class ModelSelector:
    """Unified model selector for LLM provider management.

    Handles detection, validation, and creation of LangChain chat models
    across multiple providers (OpenAI, Anthropic, xAI).
    """

    def __init__(self) -> None:
        """Initialize the model selector with an empty cache."""
        self._package_cache: Dict[str, bool] = {}

    def is_package_installed(self, provider_key: str) -> bool:
        """Check if the LangChain package for a provider is installed.

        Args:
            provider_key: Provider key (e.g., "openai", "anthropic", "xai")

        Returns:
            True if the package is installed, False otherwise
        """
        if provider_key in self._package_cache:
            return self._package_cache[provider_key]

        provider = get_provider(provider_key)
        if not provider:
            return False

        # Map provider keys to their import checks
        import_checks = {
            "openai": "langchain_openai",
            "anthropic": "langchain_anthropic",
            "xai": "langchain_xai",
        }

        module_name = import_checks.get(provider_key)
        if not module_name:
            return False

        try:
            __import__(module_name)
            self._package_cache[provider_key] = True
            return True
        except ImportError:
            self._package_cache[provider_key] = False
            return False

    def has_api_key(self, provider_key: str) -> bool:
        """Check if the API key for a provider is set in environment.

        Args:
            provider_key: Provider key (e.g., "openai", "anthropic", "xai")

        Returns:
            True if the API key is set and non-empty, False otherwise
        """
        provider = get_provider(provider_key)
        if not provider or not provider.api_key_env:
            return False

        key = os.environ.get(provider.api_key_env, "").strip()
        return bool(key)

    def detect_available_providers(self) -> List[Tuple[str, bool, bool]]:
        """Detect all providers and their availability status.

        Returns:
            List of tuples (provider_key, package_installed, api_key_set)
        """
        result = []
        for provider_key in list_providers():
            installed = self.is_package_installed(provider_key)
            has_key = self.has_api_key(provider_key)
            result.append((provider_key, installed, has_key))
        return result

    def get_default_provider(self) -> Optional[str]:
        """Get the default provider based on environment and availability.

        Priority:
        1. CYBERZARD_PROVIDER environment variable (if valid and available)
        2. CYBERZARD_MODEL_PROVIDER environment variable (legacy, if valid)
        3. First provider with both package installed and API key set

        Returns:
            Provider key if available, None otherwise
        """
        # Check explicit environment variable
        for env_var in ("CYBERZARD_PROVIDER", "CYBERZARD_MODEL_PROVIDER"):
            explicit_provider = os.environ.get(env_var, "").lower().strip()
            if explicit_provider and explicit_provider != "none":
                provider = get_provider(explicit_provider)
                if provider:
                    valid, _ = self.validate_provider(explicit_provider)
                    if valid:
                        return explicit_provider

        # Auto-detect first available provider
        for provider_key, installed, has_key in self.detect_available_providers():
            if installed and has_key:
                return provider_key

        return None

    def validate_provider(self, provider_key: str) -> Tuple[bool, str]:
        """Validate that a provider is usable.

        Args:
            provider_key: Provider key to validate

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
        """
        provider = get_provider(provider_key)
        if not provider:
            return False, f"Unknown provider: '{provider_key}'. Valid options: {', '.join(list_providers())}"

        if not self.is_package_installed(provider_key):
            return False, (
                f"Package '{provider.package}' not installed. "
                f"Install with: pip install {provider.package}"
            )

        if not self.has_api_key(provider_key):
            return False, (
                f"API key not set. Set environment variable: {provider.api_key_env}"
            )

        return True, ""

    def create_model(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        streaming: bool = True,
        **kwargs: Any,
    ):
        """Create a LangChain chat model instance.

        Args:
            provider: Provider key (auto-detected if None)
            model: Model name (uses provider default if None)
            temperature: Model temperature (default 0.7)
            streaming: Enable streaming responses (default True)
            **kwargs: Additional arguments passed to init_chat_model

        Returns:
            LangChain BaseChatModel instance

        Raises:
            ValueError: If no provider available or provider invalid
            ImportError: If langchain.chat_models not available
        """
        # Determine provider
        if provider is None:
            provider = self.get_default_provider()
            if provider is None:
                raise ValueError(
                    "No AI provider configured. "
                    "Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or XAI_API_KEY"
                )

        # Validate provider
        valid, error = self.validate_provider(provider)
        if not valid:
            raise ValueError(error)

        # Get provider info
        provider_info = get_provider(provider)
        if not provider_info:
            raise ValueError(f"Unknown provider: {provider}")

        # Determine model name
        model_name = model or provider_info.default_model

        # Import and create model
        try:
            from langchain.chat_models import init_chat_model
        except ImportError:
            raise ImportError(
                "langchain.chat_models not available. "
                "Install with: pip install langchain"
            )

        return init_chat_model(
            model_name,
            model_provider=provider_info.model_provider,
            temperature=temperature,
            streaming=streaming,
            **kwargs,
        )


# Module-level convenience instance
_selector: Optional[ModelSelector] = None


def get_selector() -> ModelSelector:
    """Get or create the global ModelSelector instance."""
    global _selector
    if _selector is None:
        _selector = ModelSelector()
    return _selector


__all__ = [
    "ModelSelector",
    "get_selector",
]
