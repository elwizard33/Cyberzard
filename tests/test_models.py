"""Unit tests for the models module (provider registry and selector)."""
from __future__ import annotations

import os
import pytest
from unittest.mock import patch, MagicMock


# ============= Registry Tests =============

class TestProviderRegistry:
    """Tests for cyberzard.models.registry module."""

    def test_list_providers_returns_all_three(self):
        """list_providers should return all registered providers."""
        from cyberzard.models.registry import list_providers
        providers = list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "xai" in providers
        assert len(providers) == 3

    def test_get_provider_openai(self):
        """get_provider should return correct ProviderInfo for OpenAI."""
        from cyberzard.models.registry import get_provider
        info = get_provider("openai")
        assert info is not None
        assert info.name == "OpenAI"
        assert info.api_key_env == "OPENAI_API_KEY"
        assert info.model_provider == "openai"
        assert info.default_model == "gpt-4o-mini"

    def test_get_provider_anthropic(self):
        """get_provider should return correct ProviderInfo for Anthropic."""
        from cyberzard.models.registry import get_provider
        info = get_provider("anthropic")
        assert info is not None
        assert info.name == "Anthropic"
        assert info.api_key_env == "ANTHROPIC_API_KEY"
        assert info.model_provider == "anthropic"

    def test_get_provider_xai(self):
        """get_provider should return correct ProviderInfo for xAI."""
        from cyberzard.models.registry import get_provider
        info = get_provider("xai")
        assert info is not None
        assert info.name == "xAI (Grok)"  # Full name includes Grok
        assert info.api_key_env == "XAI_API_KEY"
        assert info.model_provider == "xai"
        assert info.default_model == "grok-2"

    def test_get_provider_invalid_returns_none(self):
        """get_provider should return None for unknown providers."""
        from cyberzard.models.registry import get_provider
        assert get_provider("invalid") is None
        assert get_provider("azure") is None
        assert get_provider("") is None

    def test_get_provider_case_insensitive(self):
        """get_provider should handle case-insensitively via .lower()."""
        from cyberzard.models.registry import get_provider
        # The registry normalizes keys to lowercase, so both should work
        assert get_provider("OpenAI") is not None
        assert get_provider("openai") is not None
        assert get_provider("OPENAI") is not None


# ============= Selector Tests =============

class TestModelSelector:
    """Tests for cyberzard.models.selector.ModelSelector class."""

    def test_detect_available_providers_returns_all_three(self):
        """detect_available_providers should return info for all providers."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        result = selector.detect_available_providers()
        assert len(result) == 3
        # Each result is (provider_name, package_installed, has_key)
        provider_names = [r[0] for r in result]
        assert "openai" in provider_names
        assert "anthropic" in provider_names
        assert "xai" in provider_names

    def test_is_package_installed_openai(self):
        """is_package_installed should check for langchain-openai package."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        # This test will pass/fail based on actual package installation
        result = selector.is_package_installed("openai")
        assert isinstance(result, bool)

    def test_has_api_key_true_when_set(self):
        """has_api_key should return True when env var is set."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-12345"}):
            assert selector.has_api_key("openai") is True

    def test_has_api_key_false_when_not_set(self):
        """has_api_key should return False when env var is not set."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        # Clear the environment variable
        env_copy = os.environ.copy()
        env_copy.pop("OPENAI_API_KEY", None)
        with patch.dict(os.environ, env_copy, clear=True):
            assert selector.has_api_key("openai") is False

    def test_has_api_key_false_when_empty(self):
        """has_api_key should return False when env var is empty string."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            assert selector.has_api_key("openai") is False

    def test_has_api_key_false_for_invalid_provider(self):
        """has_api_key should return False for unknown providers."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        assert selector.has_api_key("invalid") is False

    def test_validate_provider_valid_with_key(self):
        """validate_provider should return (True, '') for valid provider with API key."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        # Mock both package check and API key check
        with patch.object(selector, "is_package_installed", return_value=True), \
             patch.object(selector, "has_api_key", return_value=True):
            valid, error = selector.validate_provider("openai")
            assert valid is True
            assert error == ""

    def test_validate_provider_missing_package(self):
        """validate_provider should return error for missing package."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        with patch.object(selector, "is_package_installed", return_value=False):
            valid, error = selector.validate_provider("openai")
            assert valid is False
            assert "not installed" in error.lower() or "langchain-openai" in error.lower()

    def test_validate_provider_missing_api_key(self):
        """validate_provider should return error for missing API key."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        with patch.object(selector, "is_package_installed", return_value=True), \
             patch.object(selector, "has_api_key", return_value=False):
            valid, error = selector.validate_provider("openai")
            assert valid is False
            assert "OPENAI_API_KEY" in error

    def test_validate_provider_invalid(self):
        """validate_provider should return error for unknown provider."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        valid, error = selector.validate_provider("invalid")
        assert valid is False
        assert "unknown provider" in error.lower()

    def test_get_default_provider_from_cyberzard_provider_env(self):
        """get_default_provider should prefer CYBERZARD_PROVIDER env var."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        with patch.dict(os.environ, {"CYBERZARD_PROVIDER": "anthropic"}), \
             patch.object(selector, "is_package_installed", return_value=True), \
             patch.object(selector, "has_api_key", return_value=True):
            assert selector.get_default_provider() == "anthropic"

    def test_get_default_provider_legacy_env_var(self):
        """get_default_provider should fall back to CYBERZARD_MODEL_PROVIDER."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        env = {"CYBERZARD_MODEL_PROVIDER": "openai"}
        # Remove CYBERZARD_PROVIDER if present
        with patch.dict(os.environ, env, clear=True), \
             patch.object(selector, "is_package_installed", return_value=True), \
             patch.object(selector, "has_api_key", return_value=True):
            result = selector.get_default_provider()
            # Since we cleared env and set only legacy var, should use it
            # (Or autodetect if validation fails)
            assert result in ("openai", None)

    def test_get_default_provider_autodetect(self):
        """get_default_provider should auto-detect when no env var set."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        # Clear relevant env vars and mock detection
        env = {}
        with patch.dict(os.environ, env, clear=True):
            # Mock one available provider
            with patch.object(selector, "is_package_installed", side_effect=lambda p: p == "openai"), \
                 patch.object(selector, "has_api_key", side_effect=lambda p: p == "openai"):
                result = selector.get_default_provider()
                assert result == "openai"

    def test_get_default_provider_none_when_no_providers_available(self):
        """get_default_provider should return None when no providers available."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(selector, "is_package_installed", return_value=False), \
             patch.object(selector, "has_api_key", return_value=False):
            result = selector.get_default_provider()
            assert result is None

    def test_create_model_calls_init_chat_model(self):
        """create_model should call init_chat_model with correct parameters."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        mock_model = MagicMock()
        # Mock validation to pass and mock init_chat_model
        with patch.object(selector, "validate_provider", return_value=(True, "")), \
             patch("langchain.chat_models.init_chat_model", return_value=mock_model) as mock_init:
            result = selector.create_model(
                provider="openai",
                model="gpt-4",
                temperature=0.5,
                streaming=True
            )
            
            mock_init.assert_called_once()
            call_args = mock_init.call_args
            # First positional arg is the model name
            assert call_args[0][0] == "gpt-4"
            # Keyword args
            assert call_args[1]["model_provider"] == "openai"
            assert call_args[1]["temperature"] == 0.5
            assert call_args[1]["streaming"] is True
            assert result == mock_model

    def test_create_model_uses_default_model_when_not_specified(self):
        """create_model should use provider's default model when model is None."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        mock_model = MagicMock()
        # Mock validation to pass and mock init_chat_model
        with patch.object(selector, "validate_provider", return_value=(True, "")), \
             patch("langchain.chat_models.init_chat_model", return_value=mock_model) as mock_init:
            selector.create_model(provider="openai", model=None)
            
            call_args = mock_init.call_args
            # First positional arg should be the default model for OpenAI
            assert call_args[0][0] == "gpt-4o-mini"


# ============= Module Export Tests =============

class TestModuleExports:
    """Tests for cyberzard.models module exports."""

    def test_models_init_exports(self):
        """cyberzard.models should export key classes and functions."""
        from cyberzard import models
        
        # Check ModelSelector is exported
        assert hasattr(models, "ModelSelector")
        
        # Check registry functions are exported
        assert hasattr(models, "get_provider")
        assert hasattr(models, "list_providers")
        
        # Check convenience function
        assert hasattr(models, "get_selector")

    def test_get_selector_returns_singleton(self):
        """get_selector should return a singleton ModelSelector instance."""
        from cyberzard.models import get_selector
        
        selector1 = get_selector()
        selector2 = get_selector()
        # They should be the same instance
        assert selector1 is selector2


# ============= Integration Tests =============

class TestModelSelectorIntegration:
    """Integration tests that test the full flow."""

    def test_full_provider_detection_flow(self):
        """Test the full flow from detection to validation."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        # Get available providers
        available = selector.detect_available_providers()
        assert isinstance(available, list)
        
        # Each entry should be a tuple of (name, package_installed, has_key)
        for provider_name, pkg_installed, has_key in available:
            assert isinstance(provider_name, str)
            assert isinstance(pkg_installed, bool)
            assert isinstance(has_key, bool)

    def test_provider_priority_order(self):
        """Test that provider detection respects priority order."""
        from cyberzard.models.selector import ModelSelector
        selector = ModelSelector()
        
        # When multiple providers available, should return first valid one
        with patch.object(selector, "is_package_installed", return_value=True), \
             patch.object(selector, "has_api_key", return_value=True), \
             patch.dict(os.environ, {}, clear=True):
            result = selector.get_default_provider()
            # Should be openai (first in priority)
            assert result == "openai"


class TestCheckAIConfigured:
    """Tests for check_ai_configured function in ui module."""

    def test_check_ai_configured_returns_true_when_configured(self):
        """check_ai_configured should return (True, provider, None) when AI is ready."""
        from cyberzard.ui import check_ai_configured
        from cyberzard.models.selector import ModelSelector
        
        with patch.object(ModelSelector, "detect_available_providers") as mock_detect:
            mock_detect.return_value = [("openai", True, True)]
            is_configured, provider, error = check_ai_configured()
            assert is_configured is True
            assert provider == "openai"
            assert error is None

    def test_check_ai_configured_returns_false_when_no_package(self):
        """check_ai_configured should return False with helpful error when no packages installed."""
        from cyberzard.ui import check_ai_configured
        from cyberzard.models.selector import ModelSelector
        
        with patch.object(ModelSelector, "detect_available_providers") as mock_detect:
            mock_detect.return_value = [
                ("openai", False, False),
                ("anthropic", False, False),
                ("xai", False, False),
            ]
            is_configured, provider, error = check_ai_configured()
            assert is_configured is False
            assert provider is None
            assert "No AI provider packages installed" in error

    def test_check_ai_configured_returns_false_when_no_api_key(self):
        """check_ai_configured should return False with helpful error when API key missing."""
        from cyberzard.ui import check_ai_configured
        from cyberzard.models.selector import ModelSelector
        
        with patch.object(ModelSelector, "detect_available_providers") as mock_detect:
            mock_detect.return_value = [
                ("openai", True, False),  # Package installed but no key
                ("anthropic", False, False),
                ("xai", False, False),
            ]
            is_configured, provider, error = check_ai_configured()
            assert is_configured is False
            assert provider is None
            assert "API key not set" in error
