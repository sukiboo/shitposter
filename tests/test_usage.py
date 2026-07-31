import base64
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from shitposter.providers.text_to_caption import (
    AnthropicTextToCaptionProvider,
    OpenAITextToCaptionProvider,
)
from shitposter.providers.text_to_emoji import (
    AnthropicTextToEmojiProvider,
    OpenAITextToEmojiProvider,
)
from shitposter.providers.text_to_image import OpenAIImageProvider
from shitposter.providers.text_to_int import (
    AnthropicTextToIntProvider,
    OpenAITextToIntProvider,
)
from shitposter.providers.text_to_text import AnthropicTextProvider, OpenAITextProvider

USAGE = {"input_tokens": 100, "output_tokens": 50}


@pytest.fixture(autouse=True)
def _mock_clients():
    with patch("openai.OpenAI"), patch("anthropic.Anthropic"):
        yield


def _usage(input_tokens=100, output_tokens=50):
    return SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)


def _caption(length=100):
    return "c" * length


# Each factory returns (provider, zero-arg callable that triggers one API call).
# Providers are annotated Any because the patched SDK client is a MagicMock, not
# the real typed client the constructor advertises.


def _openai_text():
    provider: Any = OpenAITextProvider()
    provider.client.responses.create.return_value = SimpleNamespace(
        output_text="ok", usage=_usage()
    )
    return provider, lambda: provider.generate("x")


def _openai_caption():
    provider: Any = OpenAITextToCaptionProvider()
    provider.client.responses.parse.return_value = SimpleNamespace(
        output_parsed=SimpleNamespace(caption=_caption()), usage=_usage()
    )
    return provider, lambda: provider.generate("x")


def _openai_int():
    provider: Any = OpenAITextToIntProvider()
    provider.client.responses.parse.return_value = SimpleNamespace(
        output_parsed=SimpleNamespace(index=1), usage=_usage()
    )
    return provider, lambda: provider.generate("x", ["a", "b"])


def _openai_emoji():
    provider: Any = OpenAITextToEmojiProvider()
    provider.client.responses.parse.return_value = SimpleNamespace(
        output_parsed=SimpleNamespace(emojis=["\U0001f389"]), usage=_usage()
    )
    return provider, lambda: provider.generate("x")


def _openai_image():
    provider: Any = OpenAIImageProvider()
    b64 = base64.b64encode(b"png-bytes").decode()
    provider.client.images.generate.return_value = SimpleNamespace(
        data=[SimpleNamespace(b64_json=b64)], usage=_usage()
    )
    return provider, lambda: provider.generate("x")


def _anthropic_text():
    provider: Any = AnthropicTextProvider()
    provider.client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="ok")], usage=_usage()
    )
    return provider, lambda: provider.generate("x")


def _anthropic_caption():
    provider: Any = AnthropicTextToCaptionProvider()
    block = SimpleNamespace(type="tool_use", input={"caption": _caption()})
    provider.client.messages.create.return_value = SimpleNamespace(content=[block], usage=_usage())
    return provider, lambda: provider.generate("x")


def _anthropic_int():
    provider: Any = AnthropicTextToIntProvider()
    block = SimpleNamespace(type="tool_use", input={"index": 1})
    provider.client.messages.create.return_value = SimpleNamespace(content=[block], usage=_usage())
    return provider, lambda: provider.generate("x", ["a", "b"])


def _anthropic_emoji():
    provider: Any = AnthropicTextToEmojiProvider()
    block = SimpleNamespace(type="tool_use", input={"emojis": ["\U0001f389"]})
    provider.client.messages.create.return_value = SimpleNamespace(content=[block], usage=_usage())
    return provider, lambda: provider.generate("x")


PROVIDER_FACTORIES = {
    "openai_text": _openai_text,
    "openai_caption": _openai_caption,
    "openai_int": _openai_int,
    "openai_emoji": _openai_emoji,
    "openai_image": _openai_image,
    "anthropic_text": _anthropic_text,
    "anthropic_caption": _anthropic_caption,
    "anthropic_int": _anthropic_int,
    "anthropic_emoji": _anthropic_emoji,
}


class TestUsageRecorded:
    """Every provider must route its API calls through _api_call."""

    @pytest.mark.parametrize("factory", PROVIDER_FACTORIES.values(), ids=PROVIDER_FACTORIES.keys())
    def test_generate_records_usage(self, factory):
        provider, run = factory()
        run()
        assert provider.metadata()["usage"] == [USAGE]

    @pytest.mark.parametrize("factory", PROVIDER_FACTORIES.values(), ids=PROVIDER_FACTORIES.keys())
    def test_no_usage_before_any_call(self, factory):
        provider, _ = factory()
        assert "usage" not in provider.metadata()


class TestApiCall:
    def test_returns_response_unchanged(self):
        provider = OpenAITextProvider()
        response = SimpleNamespace(output_text="ok", usage=_usage())
        assert provider._api_call(lambda **kw: response) is response

    def test_forwards_kwargs(self):
        provider = OpenAITextProvider()
        seen = {}

        def api(**kwargs):
            seen.update(kwargs)
            return SimpleNamespace(usage=_usage())

        provider._api_call(api, model="m", input="p")
        assert seen == {"model": "m", "input": "p"}

    def test_response_without_usage_attribute(self):
        provider = OpenAITextProvider()
        provider._api_call(lambda **kw: SimpleNamespace(output_text="ok"))
        assert "usage" not in provider.metadata()

    def test_usage_is_none(self):
        provider = OpenAITextProvider()
        provider._api_call(lambda **kw: SimpleNamespace(output_text="ok", usage=None))
        assert "usage" not in provider.metadata()

    def test_one_entry_per_call(self):
        provider = OpenAITextProvider()
        responses = iter([SimpleNamespace(usage=_usage(5, out)) for out in (10, 20, 30)])
        for _ in range(3):
            provider._api_call(lambda **kw: next(responses))
        assert provider.metadata()["usage"] == [
            {"input_tokens": 5, "output_tokens": 10},
            {"input_tokens": 5, "output_tokens": 20},
            {"input_tokens": 5, "output_tokens": 30},
        ]


class TestUsageAcrossRetries:
    def test_failed_attempt_is_still_recorded(self):
        provider: Any = AnthropicTextToIntProvider()
        responses = [
            SimpleNamespace(
                content=[SimpleNamespace(type="tool_use", input={"index": 99})],
                usage=_usage(500, 40),
            ),
            SimpleNamespace(
                content=[SimpleNamespace(type="tool_use", input={"index": 2})],
                usage=_usage(500, 60),
            ),
        ]
        provider.client.messages.create.side_effect = lambda **kw: responses.pop(0)

        assert provider.generate("pick", ["a", "b", "c"]) == 1
        assert provider.metadata()["usage"] == [
            {"input_tokens": 500, "output_tokens": 40},
            {"input_tokens": 500, "output_tokens": 60},
        ]

    def test_unstructured_fallback_is_recorded(self):
        provider: Any = AnthropicTextToCaptionProvider()
        short = SimpleNamespace(type="tool_use", input={"caption": "too short"})
        fallback = SimpleNamespace(type="text", text=_caption())

        def side_effect(**kwargs):
            if "tools" in kwargs:
                return SimpleNamespace(content=[short], usage=_usage(200, 30))
            return SimpleNamespace(content=[fallback], usage=_usage(200, 80))

        provider.client.messages.create.side_effect = side_effect

        provider.generate("caption this")
        usage = provider.metadata()["usage"]
        assert len(usage) == provider.MAX_RETRIES + 1
        assert usage[-1] == {"input_tokens": 200, "output_tokens": 80}
