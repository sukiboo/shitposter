from unittest.mock import MagicMock, patch

import pytest

from shitposter.providers.text_to_caption import AnthropicTextToCaptionProvider
from shitposter.providers.text_to_emoji import AnthropicTextToEmojiProvider
from shitposter.providers.text_to_int import AnthropicTextToIntProvider
from shitposter.providers.text_to_text import AnthropicTextProvider

ALLOWED_MODELS = [
    "claude-opus-5",
    "claude-opus-4-8",
    "claude-opus-4-6",
    "claude-sonnet-5",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-haiku-4-5-20251001",
]


@pytest.fixture(autouse=True)
def _mock_anthropic():
    with patch("anthropic.Anthropic"):
        yield


# --- AnthropicTextProvider ---


class TestAnthropicTextValidation:
    @pytest.mark.parametrize("model", ALLOWED_MODELS)
    def test_allowed_models(self, model):
        provider = AnthropicTextProvider(model=model)
        assert provider.model == model

    def test_default_model(self):
        provider = AnthropicTextProvider()
        assert provider.model == "claude-sonnet-4-6"

    @pytest.mark.parametrize("model", ["gpt-5", "llama-3", "claude-2"])
    def test_rejects_unsupported_model(self, model):
        with pytest.raises(ValueError, match=f"Unsupported model '{model}'"):
            AnthropicTextProvider(model=model)

    def test_default_max_tokens(self):
        provider = AnthropicTextProvider()
        assert provider.max_tokens == 1024

    def test_custom_max_tokens(self):
        provider = AnthropicTextProvider(max_tokens=2048)
        assert provider.max_tokens == 2048


class TestAnthropicTextBudgetTokens:
    def test_default_no_budget(self):
        provider = AnthropicTextProvider()
        assert provider.budget_tokens is None

    def test_custom_budget(self):
        provider = AnthropicTextProvider(max_tokens=4096, budget_tokens=2048)
        assert provider.budget_tokens == 2048

    def test_rejects_budget_below_minimum(self):
        with pytest.raises(ValueError, match="budget_tokens must be at least 1024"):
            AnthropicTextProvider(max_tokens=4096, budget_tokens=512)

    def test_rejects_budget_gte_max_tokens(self):
        with pytest.raises(ValueError, match="max_tokens must be greater than budget_tokens"):
            AnthropicTextProvider(max_tokens=2048, budget_tokens=2048)

        with pytest.raises(ValueError, match="max_tokens must be greater than budget_tokens"):
            AnthropicTextProvider(max_tokens=2048, budget_tokens=4096)


class TestAnthropicThinkingValidation:
    def test_rejects_budget_tokens_on_adaptive_model(self):
        with pytest.raises(ValueError, match="rejects budget_tokens"):
            AnthropicTextProvider(model="claude-sonnet-5", max_tokens=4096, budget_tokens=2048)

    def test_rejects_effort_on_model_without_support(self):
        with pytest.raises(ValueError, match="does not support effort"):
            AnthropicTextProvider(model="claude-haiku-4-5", effort="high")

    def test_rejects_unknown_effort(self):
        with pytest.raises(ValueError, match="Unsupported effort 'turbo'"):
            AnthropicTextProvider(model="claude-sonnet-5", effort="turbo")

    def test_accepts_effort_on_supported_model(self):
        provider = AnthropicTextProvider(model="claude-sonnet-4-6", effort="max")
        assert provider.effort == "max"


class TestAnthropicTextMetadata:
    def test_metadata_without_budget(self):
        provider = AnthropicTextProvider()
        meta = provider.metadata()
        assert meta["provider"] == "anthropic"
        assert meta["model"] == "claude-sonnet-4-6"
        assert meta["max_tokens"] == 1024
        assert "budget_tokens" not in meta

    def test_metadata_with_budget(self):
        provider = AnthropicTextProvider(max_tokens=4096, budget_tokens=2048)
        meta = provider.metadata()
        assert meta["budget_tokens"] == 2048


class TestAnthropicTextGenerate:
    def test_generate_returns_text(self):
        provider = AnthropicTextProvider()
        text_block = MagicMock(type="text", text="hello world")
        provider.client.messages.create.return_value.content = [text_block]

        assert provider.generate("say hello") == "hello world"

    def test_generate_skips_thinking_blocks(self):
        provider = AnthropicTextProvider(max_tokens=4096, budget_tokens=2048)
        thinking_block = MagicMock(type="thinking")
        text_block = MagicMock(type="text", text="result")
        provider.client.messages.create.return_value.content = [thinking_block, text_block]

        assert provider.generate("think about this") == "result"

    def test_generate_passes_thinking_when_budget_set(self):
        provider = AnthropicTextProvider(max_tokens=4096, budget_tokens=2048)
        text_block = MagicMock(type="text", text="ok")
        provider.client.messages.create.return_value.content = [text_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["thinking"] == {"type": "enabled", "budget_tokens": 2048}

    def test_generate_passes_adaptive_thinking_on_newer_model(self):
        provider = AnthropicTextProvider(model="claude-sonnet-5")
        text_block = MagicMock(type="text", text="ok")
        provider.client.messages.create.return_value.content = [text_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["thinking"] == {"type": "adaptive"}
        assert "budget_tokens" not in call_kwargs["thinking"]

    def test_generate_passes_effort_on_newer_model(self):
        provider = AnthropicTextProvider(model="claude-sonnet-5", effort="high")
        text_block = MagicMock(type="text", text="ok")
        provider.client.messages.create.return_value.content = [text_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["output_config"] == {"effort": "high"}

    def test_generate_no_thinking_without_budget(self):
        provider = AnthropicTextProvider()
        text_block = MagicMock(type="text", text="ok")
        provider.client.messages.create.return_value.content = [text_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert "thinking" not in call_kwargs


# --- AnthropicTextToCaptionProvider ---


class TestAnthropicCaptionValidation:
    @pytest.mark.parametrize("model", ALLOWED_MODELS)
    def test_allowed_models(self, model):
        provider = AnthropicTextToCaptionProvider(model=model)
        assert provider.model == model

    def test_rejects_unsupported_model(self):
        with pytest.raises(ValueError, match="Unsupported model"):
            AnthropicTextToCaptionProvider(model="gpt-5")

    def test_budget_tokens_validation(self):
        with pytest.raises(ValueError, match="budget_tokens must be at least 1024"):
            AnthropicTextToCaptionProvider(max_tokens=4096, budget_tokens=100)


class TestAnthropicCaptionGenerate:
    def test_returns_caption_from_tool_use(self):
        provider = AnthropicTextToCaptionProvider()
        tool_block = MagicMock(type="tool_use", input={"caption": "a" * 100})
        provider.client.messages.create.return_value.content = [tool_block]

        assert provider.generate("make a caption") == "a" * 100

    def test_accepts_short_punchy_caption(self):
        provider = AnthropicTextToCaptionProvider()
        caption = "Tiny paws, huge liability 😬"
        tool_block = MagicMock(type="tool_use", input={"caption": caption})
        provider.client.messages.create.return_value.content = [tool_block]

        assert provider.generate("make a caption") == caption

    def test_rejects_caption_too_short(self):
        provider = AnthropicTextToCaptionProvider()
        short_block = MagicMock(type="tool_use", input={"caption": "too short"})
        fallback_block = MagicMock(type="text", text="fallback caption")

        provider.client.messages.create.return_value.content = [short_block]

        def side_effect(**kwargs):
            resp = MagicMock()
            if "tools" in kwargs:
                resp.content = [short_block]
            else:
                resp.content = [fallback_block]
            return resp

        provider.client.messages.create.side_effect = side_effect

        result = provider.generate("make a caption")
        assert result == "fallback caption"

    def test_forced_tool_choice_without_budget(self):
        provider = AnthropicTextToCaptionProvider()
        tool_block = MagicMock(type="tool_use", input={"caption": "x" * 100})
        provider.client.messages.create.return_value.content = [tool_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "caption"}
        assert "thinking" not in call_kwargs

    def test_auto_tool_choice_with_budget(self):
        provider = AnthropicTextToCaptionProvider(max_tokens=4096, budget_tokens=2048)
        tool_block = MagicMock(type="tool_use", input={"caption": "x" * 100})
        provider.client.messages.create.return_value.content = [tool_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "auto"}
        assert call_kwargs["thinking"] == {"type": "enabled", "budget_tokens": 2048}


# --- AnthropicTextToEmojiProvider ---


class TestAnthropicEmojiValidation:
    @pytest.mark.parametrize("model", ALLOWED_MODELS)
    def test_allowed_models(self, model):
        provider = AnthropicTextToEmojiProvider(model=model)
        assert provider.model == model

    def test_rejects_unsupported_model(self):
        with pytest.raises(ValueError, match="Unsupported model"):
            AnthropicTextToEmojiProvider(model="gpt-5")


class TestAnthropicEmojiGenerate:
    def test_returns_joined_emojis(self):
        provider = AnthropicTextToEmojiProvider()
        tool_block = MagicMock(type="tool_use", input={"emojis": ["\U0001f389", "\U0001f600"]})
        provider.client.messages.create.return_value.content = [tool_block]

        assert provider.generate("pick emojis") == "\U0001f389\U0001f600"

    def test_rejects_non_emoji_and_falls_back(self):
        provider = AnthropicTextToEmojiProvider()
        bad_block = MagicMock(type="tool_use", input={"emojis": ["abc"]})
        provider.client.messages.create.return_value.content = [bad_block]

        result = provider.generate("pick emojis")
        assert result == "\U0001f389"

    def test_rejects_wrong_count_and_falls_back(self):
        provider = AnthropicTextToEmojiProvider()
        bad_block = MagicMock(
            type="tool_use",
            input={"emojis": ["\U0001f389"] * 5},
        )
        provider.client.messages.create.return_value.content = [bad_block]

        result = provider.generate("pick emojis")
        assert result == "\U0001f389"

    def test_forced_tool_choice_without_budget(self):
        provider = AnthropicTextToEmojiProvider()
        tool_block = MagicMock(type="tool_use", input={"emojis": ["\U0001f389"]})
        provider.client.messages.create.return_value.content = [tool_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "emojis"}

    def test_auto_tool_choice_with_budget(self):
        provider = AnthropicTextToEmojiProvider(max_tokens=4096, budget_tokens=2048)
        tool_block = MagicMock(type="tool_use", input={"emojis": ["\U0001f389"]})
        provider.client.messages.create.return_value.content = [tool_block]

        provider.generate("test")

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "auto"}
        assert call_kwargs["thinking"] == {"type": "enabled", "budget_tokens": 2048}


# --- AnthropicTextToIntProvider ---


class TestAnthropicIntValidation:
    @pytest.mark.parametrize("model", ALLOWED_MODELS)
    def test_allowed_models(self, model):
        provider = AnthropicTextToIntProvider(model=model)
        assert provider.model == model

    def test_rejects_unsupported_model(self):
        with pytest.raises(ValueError, match="Unsupported model"):
            AnthropicTextToIntProvider(model="gpt-5")


class TestAnthropicIntGenerate:
    def test_returns_zero_indexed(self):
        provider = AnthropicTextToIntProvider()
        tool_block = MagicMock(type="tool_use", input={"index": 2})
        provider.client.messages.create.return_value.content = [tool_block]

        assert provider.generate("pick one", ["a", "b", "c"]) == 1

    def test_rejects_out_of_range_and_falls_back(self):
        provider = AnthropicTextToIntProvider()
        bad_block = MagicMock(type="tool_use", input={"index": 99})
        provider.client.messages.create.return_value.content = [bad_block]

        result = provider.generate("pick one", ["a", "b", "c"])
        assert 0 <= result <= 2

    def test_forced_tool_choice_without_budget(self):
        provider = AnthropicTextToIntProvider()
        tool_block = MagicMock(type="tool_use", input={"index": 1})
        provider.client.messages.create.return_value.content = [tool_block]

        provider.generate("pick", ["a"])

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "choose"}

    def test_auto_tool_choice_with_budget(self):
        provider = AnthropicTextToIntProvider(max_tokens=4096, budget_tokens=2048)
        tool_block = MagicMock(type="tool_use", input={"index": 1})
        provider.client.messages.create.return_value.content = [tool_block]

        provider.generate("pick", ["a"])

        call_kwargs = provider.client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "auto"}
        assert call_kwargs["thinking"] == {"type": "enabled", "budget_tokens": 2048}
