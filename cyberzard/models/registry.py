"""Provider registry for supported LLM providers.

This module defines the metadata for all supported AI model providers,
including their LangChain package names, API key environment variables,
default models, and capability flags.

Supported providers:
- OpenAI (GPT models)
- Anthropic (Claude models)
- xAI (Grok models)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ProviderInfo:
    """Metadata for a supported LLM provider.

    Attributes:
        name: Human-readable provider name (e.g., "OpenAI")
        package: LangChain package name (e.g., "langchain-openai")
        model_provider: Provider string for init_chat_model (e.g., "openai")
        api_key_env: Environment variable name for API key (e.g., "OPENAI_API_KEY")
        default_model: Default model name for this provider
        supports_streaming: Whether the provider supports streaming responses
        supports_tools: Whether the provider supports tool/function calling
    """

    name: str
    package: str
    model_provider: str
    api_key_env: Optional[str]
    default_model: str
    supports_streaming: bool = True
    supports_tools: bool = True


# Registry of all supported providers
PROVIDERS: Dict[str, ProviderInfo] = {
    "openai": ProviderInfo(
        name="OpenAI",
        package="langchain-openai",
        model_provider="openai",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
        supports_streaming=True,
        supports_tools=True,
    ),
    "anthropic": ProviderInfo(
        name="Anthropic",
        package="langchain-anthropic",
        model_provider="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-3-haiku-20240307",
        supports_streaming=True,
        supports_tools=True,
    ),
    "xai": ProviderInfo(
        name="xAI (Grok)",
        package="langchain-xai",
        model_provider="xai",
        api_key_env="XAI_API_KEY",
        default_model="grok-2",
        supports_streaming=True,
        supports_tools=True,
    ),
}


def get_provider(name: str) -> Optional[ProviderInfo]:
    """Get provider info by name.

    Args:
        name: Provider key (e.g., "openai", "anthropic", "xai")

    Returns:
        ProviderInfo if found, None otherwise
    """
    return PROVIDERS.get(name.lower().strip())


def list_providers() -> List[str]:
    """List all supported provider keys.

    Returns:
        List of provider keys (e.g., ["openai", "anthropic", "xai"])
    """
    return list(PROVIDERS.keys())


__all__ = [
    "ProviderInfo",
    "PROVIDERS",
    "get_provider",
    "list_providers",
]
