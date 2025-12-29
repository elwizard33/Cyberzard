"""Model selector and provider registry for Cyberzard.

This module provides a unified interface for managing LLM providers
(OpenAI, Anthropic, xAI/Grok) with auto-detection, validation, and
model creation capabilities.
"""

from .registry import (
    ProviderInfo,
    PROVIDERS,
    get_provider,
    list_providers,
)
from .selector import (
    ModelSelector,
    get_selector,
)

__all__ = [
    "ProviderInfo",
    "PROVIDERS",
    "get_provider",
    "list_providers",
    "ModelSelector",
    "get_selector",
]
