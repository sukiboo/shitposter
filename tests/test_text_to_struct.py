from unittest.mock import patch

import pytest

from shitposter.providers.text_to_struct import (
    OpenAITextToEmojiProvider,
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


class TestEmojiValidation:
    @pytest.mark.parametrize(
        "emoji",
        [
            "\U0001f389",  # 🎉
            "\U0001f5f3\ufe0f",  # 🗳️ (with variation selector)
            "\U0001f1fa\U0001f1f8",  # 🇺🇸 (flag, regional indicators)
            "\U0001f1fa\U0001f1f8\U0001f985\U0001f389",  # 🇺🇸🦅🎉
            "\U0001f468\u200d\U0001f469\u200d\U0001f467",  # 👨‍👩‍👧 (ZWJ compound)
            "\U0001f44b\U0001f3fd",  # 👋🏽 (skin tone modifier)
        ],
    )
    def test_accepts_valid_emoji(self, emoji):
        assert OpenAITextToEmojiProvider._EMOJI_RE.match(emoji)

    @pytest.mark.parametrize("text", ["abc", "hello 🎉", " "])
    def test_rejects_non_emoji(self, text):
        assert not OpenAITextToEmojiProvider._EMOJI_RE.match(text)
