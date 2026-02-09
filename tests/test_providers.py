from unittest.mock import patch

import pytest

from shitposter.clients.text_to_image import OpenAIImageProvider, RandomImageProvider
from shitposter.clients.text_to_text import OpenAITextProvider

IMAGE_DEFAULTS = {"model": "gpt-image-1-mini", "width": 1024, "height": 1024, "quality": "medium"}
CAPTION_DEFAULTS = {"model": "gpt-5-nano", "temperature": 1.0}


@pytest.fixture(autouse=True)
def _mock_openai():
    with patch("openai.OpenAI"):
        yield


class TestOpenAIModelValidation:
    @pytest.mark.parametrize("model", ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"])
    def test_allowed_models(self, model):
        provider = OpenAIImageProvider(**{**IMAGE_DEFAULTS, "model": model})
        assert provider.model == model

    def test_default_model(self):
        provider = OpenAIImageProvider(**IMAGE_DEFAULTS)
        assert provider.model == "gpt-image-1-mini"

    @pytest.mark.parametrize("model", ["dall-e-3", "dall-e-2", "sd-xl"])
    def test_rejects_unsupported_model(self, model):
        with pytest.raises(ValueError, match=f"Unsupported model '{model}'"):
            OpenAIImageProvider(**{**IMAGE_DEFAULTS, "model": model})


class TestOpenAISizeValidation:
    @pytest.mark.parametrize(
        "width, height",
        [(1024, 1024), (1536, 1024), (1024, 1536)],
    )
    def test_allowed_sizes(self, width, height):
        provider = OpenAIImageProvider(**{**IMAGE_DEFAULTS, "width": width, "height": height})
        assert provider.width == width
        assert provider.height == height

    def test_default_size(self):
        provider = OpenAIImageProvider(**IMAGE_DEFAULTS)
        assert provider.width == 1024
        assert provider.height == 1024

    @pytest.mark.parametrize(
        "width, height",
        [(512, 512), (256, 256), (1920, 1080), (1536, 1536)],
    )
    def test_rejects_unsupported_size(self, width, height):
        with pytest.raises(ValueError, match=f"OpenAI does not support {width}x{height}"):
            OpenAIImageProvider(**{**IMAGE_DEFAULTS, "width": width, "height": height})


class TestCaptionModelValidation:
    @pytest.mark.parametrize(
        "model",
        ["gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"],
    )
    def test_allowed_models(self, model):
        provider = OpenAITextProvider(**{**CAPTION_DEFAULTS, "model": model})
        assert provider.model == model

    def test_default_model(self):
        provider = OpenAITextProvider(**CAPTION_DEFAULTS)
        assert provider.model == "gpt-5-nano"

    @pytest.mark.parametrize("model", ["gpt-3.5-turbo", "claude-3", "llama-3"])
    def test_rejects_unsupported_model(self, model):
        with pytest.raises(ValueError, match=f"Unsupported model '{model}'"):
            OpenAITextProvider(**{**CAPTION_DEFAULTS, "model": model})


class TestCaptionTemperature:
    def test_default_temperature(self):
        provider = OpenAITextProvider(**CAPTION_DEFAULTS)
        assert provider.temperature == 1.0

    def test_custom_temperature(self):
        provider = OpenAITextProvider(**{**CAPTION_DEFAULTS, "temperature": 0.5})
        assert provider.temperature == 0.5

    def test_zero_temperature(self):
        provider = OpenAITextProvider(**{**CAPTION_DEFAULTS, "temperature": 0.0})
        assert provider.temperature == 0.0


class TestProviderDefaults:
    def test_openai_image_defaults_without_kwargs(self):
        provider = OpenAIImageProvider()
        assert provider.model == "gpt-image-1-mini"
        assert provider.width == 1024
        assert provider.height == 1024
        assert provider.quality == "medium"

    def test_openai_caption_defaults_without_kwargs(self):
        provider = OpenAITextProvider()
        assert provider.model == "gpt-5-nano"
        assert provider.temperature == 1.0

    def test_random_image_default_size(self):
        provider = RandomImageProvider()
        assert provider.width == 512
        assert provider.height == 512
