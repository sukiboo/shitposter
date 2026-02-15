from unittest.mock import patch

import pytest

from shitposter.providers.text_to_struct import (
    OpenAITextToIntProvider,
    PlaceholderTextToIntProvider,
)


class TestPlaceholder:
    def test_returns_zero(self):
        provider = PlaceholderTextToIntProvider()
        assert provider.generate("pick one", ["a", "b", "c"]) == 0

    def test_metadata(self):
        provider = PlaceholderTextToIntProvider()
        assert provider.metadata() == {"provider": "placeholder"}


@pytest.fixture(autouse=True)
def _mock_openai():
    with patch("openai.OpenAI"):
        yield


class TestOpenAIModelValidation:
    @pytest.mark.parametrize("model", ["gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"])
    def test_allowed_models(self, model):
        provider = OpenAITextToIntProvider(model=model)
        assert provider.model == model

    def test_default_model(self):
        provider = OpenAITextToIntProvider()
        assert provider.model == "gpt-5-nano"

    @pytest.mark.parametrize("model", ["gpt-3.5-turbo", "claude-3", "llama-3"])
    def test_rejects_unsupported_model(self, model):
        with pytest.raises(ValueError, match=f"Unsupported model '{model}'"):
            OpenAITextToIntProvider(model=model)
