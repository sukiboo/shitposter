from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from shitposter.providers.text_to_emoji import EMOJI_RE
from shitposter.providers.text_to_int import (
    JevTextToIntProvider,
    OpenAITextToIntProvider,
    PlaceholderTextToIntProvider,
)


class TestPlaceholder:
    def test_returns_zero(self):
        provider = PlaceholderTextToIntProvider()
        assert provider.generate("pick one", {"a": "A.", "b": "B.", "c": "C."}) == 0

    def test_metadata(self):
        provider = PlaceholderTextToIntProvider()
        assert provider.metadata() == {"provider": "placeholder"}


def _jev_provider(probabilities: dict[str, float]) -> Any:
    with patch("typesafe_sdk.TypeSafeClient"):
        provider: Any = JevTextToIntProvider()
    choice = max(probabilities, key=lambda label: probabilities[label])
    answer = SimpleNamespace(choice=choice, confidence=0.8, probabilities=probabilities)
    provider.client.system_one.return_value = SimpleNamespace(
        choices={"choice": answer},
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )
    return provider


class TestJev:
    def test_samples_from_choice_probabilities(self):
        entries = {"Day A": "About A.", "Day B": "About B."}
        probabilities = {"Day A": 0.1, "Day B": 0.9}
        provider = _jev_provider(probabilities)

        # The sampled entry wins even when it is not the top choice.
        with patch("random.choices", return_value=["Day A"]) as choices:
            assert provider.generate("rules", entries, "history") == 0
        choices.assert_called_once_with(["Day A", "Day B"], weights=[0.1, 0.9])

        call_kwargs = provider.client.system_one.call_args.kwargs
        assert call_kwargs["state"] == "history"
        assert call_kwargs["questions"]["choice"]["instructions"] == "rules"
        assert call_kwargs["questions"]["choice"]["criteria"] == entries
        assert provider.metadata() == {
            "provider": "jev",
            "model": "jev-latest",
            "usage": [{"input_tokens": 100, "output_tokens": 50}],
            "confidence": [0.8],
            "probabilities": [probabilities],
        }

    def test_defaults_without_prompt_or_context(self):
        provider = _jev_provider({"Day A": 1.0})

        assert provider.generate("", {"Day A": "About A."}) == 0

        call_kwargs = provider.client.system_one.call_args.kwargs
        assert call_kwargs["state"] == ""
        assert call_kwargs["model"] == "jev-latest"
        instructions = call_kwargs["questions"]["choice"]["instructions"]
        assert instructions == JevTextToIntProvider.default_prompt

    def test_falls_back_to_random_on_api_error(self):
        provider = _jev_provider({"Day A": 1.0})
        provider.client.system_one.side_effect = RuntimeError("TypeSafe is down")
        entries = {"Day A": "About A.", "Day B": "About B.", "Day C": "About C."}

        with patch("random.randint", return_value=2) as randint:
            assert provider.generate("rules", entries) == 2

        randint.assert_called_once_with(0, 2)
        assert provider.metadata() == {
            "provider": "jev",
            "model": "jev-latest",
            "errors": ["TypeSafe is down", "request failed, fell back to random"],
        }


@pytest.fixture(autouse=True)
def _mock_openai():
    with patch("openai.OpenAI"):
        yield


class TestOpenAIModelValidation:
    @pytest.mark.parametrize(
        "model", ["gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2", "gpt-5.6-terra"]
    )
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


class TestOpenAIPrompt:
    def test_joins_rules_context_and_numbered_entries(self):
        provider: Any = OpenAITextToIntProvider()
        provider.client.responses.parse.return_value = SimpleNamespace(
            output_parsed=SimpleNamespace(index=2), usage=None
        )
        entries = {"Day A": "About A.", "Day B": "About B."}

        assert provider.generate("rules", entries, "history") == 1

        prompt = provider.client.responses.parse.call_args.kwargs["input"]
        assert prompt == "rules\n\nhistory\n\n1. Day A\n2. Day B"

    def test_omits_empty_context(self):
        provider: Any = OpenAITextToIntProvider()
        provider.client.responses.parse.return_value = SimpleNamespace(
            output_parsed=SimpleNamespace(index=1), usage=None
        )

        provider.generate("rules", {"Day A": "About A."})

        prompt = provider.client.responses.parse.call_args.kwargs["input"]
        assert prompt == "rules\n\n1. Day A"


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
        assert EMOJI_RE.match(emoji)

    @pytest.mark.parametrize("text", ["abc", "hello 🎉", " "])
    def test_rejects_non_emoji(self, text):
        assert not EMOJI_RE.match(text)
