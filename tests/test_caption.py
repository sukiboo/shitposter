import base64
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from shitposter.providers.text_to_caption import (
    AnthropicTextToCaptionProvider,
    OpenAITextToCaptionProvider,
    PlaceholderTextToCaptionProvider,
)
from shitposter.steps.generate_text import GenerateCaptionStep

HOLIDAY = "World Egg Day"
PROMPT = "Caption for World Egg Day."
CAPTION = "Nobody tell him kittens don't come in shells."
PNG_SIZE = (1, 1)


@pytest.fixture(autouse=True)
def _mock_clients():
    with patch("openai.OpenAI"), patch("anthropic.Anthropic"):
        yield


@pytest.fixture
def image_path(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", PNG_SIZE).save(path)
    return str(path)


@pytest.fixture(params=[OpenAITextToCaptionProvider, AnthropicTextToCaptionProvider])
def provider(request):
    instance = request.param()
    if isinstance(instance, OpenAITextToCaptionProvider):
        instance.client.responses.parse.return_value = SimpleNamespace(
            output_parsed=SimpleNamespace(caption=CAPTION), usage=None
        )
    else:
        instance.client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="tool_use", input={"caption": CAPTION})], usage=None
        )
    return instance


def _request_calls(provider):
    if isinstance(provider, OpenAITextToCaptionProvider):
        return (
            provider.client.responses.parse.call_args_list
            + provider.client.responses.create.call_args_list
        )
    return provider.client.messages.create.call_args_list


def _assert_request_content(provider, kwargs, image_data):
    assert kwargs["model"] == provider.model
    if isinstance(provider, OpenAITextToCaptionProvider):
        assert kwargs["reasoning"] == {"effort": provider.effort}
        if image_data is None:
            assert kwargs["input"] == PROMPT
            return
        messages = kwargs["input"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        content = messages[0]["content"]
        assert len(content) == 2
        assert content[0] == {"type": "input_text", "text": PROMPT}
        assert content[1]["type"] == "input_image"
        assert content[1]["detail"] == "auto"
        prefix, encoded = content[1]["image_url"].split(",", 1)
        assert prefix == "data:image/png;base64"
        assert base64.b64decode(encoded) == image_data
    else:
        assert kwargs["max_tokens"] == provider.max_tokens
        if image_data is None:
            assert kwargs["messages"] == [{"role": "user", "content": PROMPT}]
            return
        messages = kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        content = messages[0]["content"]
        assert len(content) == 2
        assert content[0] == {"type": "text", "text": PROMPT}
        assert content[1]["type"] == "image"
        source = content[1]["source"]
        assert source["type"] == "base64"
        assert source["media_type"] == "image/png"
        assert base64.b64decode(source["data"]) == image_data


@pytest.mark.parametrize("with_image", [False, True])
def test_caption_request(provider, image_path, with_image):
    path = image_path if with_image else None
    image_data = Path(path).read_bytes() if path else None

    assert provider.generate(PROMPT, image_path=path) == CAPTION

    calls = _request_calls(provider)
    assert len(calls) == 1
    _assert_request_content(provider, calls[0].kwargs, image_data)
    if isinstance(provider, OpenAITextToCaptionProvider):
        assert calls[0].kwargs["text_format"] is provider._CaptionResponse
    else:
        assert calls[0].kwargs["tools"] == [provider._TOOL]
        assert calls[0].kwargs["tool_choice"] == {"type": "tool", "name": "caption"}


def test_caption_retry_keeps_image(provider, image_path):
    api = (
        provider.client.responses.parse
        if isinstance(provider, OpenAITextToCaptionProvider)
        else provider.client.messages.create
    )
    api.side_effect = [RuntimeError("temporary failure"), api.return_value]

    assert provider.generate(PROMPT, image_path=image_path) == CAPTION

    calls = _request_calls(provider)
    assert len(calls) == 2
    for call in calls:
        _assert_request_content(provider, call.kwargs, Path(image_path).read_bytes())
    assert calls[0].kwargs == calls[1].kwargs


@pytest.mark.parametrize("with_image", [False, True])
def test_caption_fallback_keeps_inputs(provider, image_path, with_image):
    path = image_path if with_image else None
    image_data = Path(path).read_bytes() if path else None
    if isinstance(provider, OpenAITextToCaptionProvider):
        provider.client.responses.parse.side_effect = RuntimeError("structured output failed")
        provider.client.responses.create.return_value = SimpleNamespace(
            output_text=CAPTION, usage=None
        )
    else:
        fallback = SimpleNamespace(content=[SimpleNamespace(type="text", text=CAPTION)], usage=None)
        provider.client.messages.create.side_effect = [
            RuntimeError("tool output failed")
        ] * provider.MAX_RETRIES + [fallback]

    assert provider.generate(PROMPT, image_path=path) == CAPTION

    calls = _request_calls(provider)
    assert len(calls) == provider.MAX_RETRIES + 1
    for call in calls:
        _assert_request_content(provider, call.kwargs, image_data)
    if isinstance(provider, OpenAITextToCaptionProvider):
        for call in calls[:-1]:
            assert call.kwargs["text_format"] is provider._CaptionResponse
        assert "text_format" not in calls[-1].kwargs
    else:
        for call in calls[:-1]:
            assert call.kwargs["tools"] == [provider._TOOL]
        assert "tools" not in calls[-1].kwargs
        assert "tool_choice" not in calls[-1].kwargs


def test_missing_image_fails_before_api_call(provider, tmp_path):
    path = tmp_path / "missing.png"

    with pytest.raises(FileNotFoundError, match="missing.png"):
        provider.generate(PROMPT, image_path=str(path))

    assert _request_calls(provider) == []


@pytest.mark.parametrize("with_image", [False, True])
def test_placeholder_caption_accepts_optional_image(image_path, with_image):
    provider = PlaceholderTextToCaptionProvider()

    assert provider.generate(PROMPT, image_path=image_path if with_image else None) == (
        "Placeholder caption."
    )


@pytest.mark.parametrize("with_image", [False, True])
def test_caption_step_forwards_image_and_records_artifact(run_ctx, image_path, with_image):
    run_ctx.state.update(holiday=HOLIDAY, image=image_path, prompt="Unused image-generation prompt")
    inputs = ["holiday", "image"] if with_image else ["holiday"]
    step = GenerateCaptionStep(
        run_ctx,
        {"provider": "placeholder", "inputs": inputs, "template": "Caption for {holiday}."},
        "caption",
        0,
    )
    step.provider.generate = Mock(return_value=CAPTION)

    result = step.execute()

    step.provider.generate.assert_called_once_with(
        PROMPT, image_path=image_path if with_image else None
    )
    assert run_ctx.state["caption"] == CAPTION
    assert result.summary == repr(CAPTION)
    artifact = json.loads((run_ctx.run_dir / "0_caption.json").read_text())
    assert artifact["inputs"] == {name: run_ctx.state[name] for name in inputs}
    assert artifact["prompt"] == PROMPT
    assert artifact["output"] == CAPTION
