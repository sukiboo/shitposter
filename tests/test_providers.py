from unittest.mock import patch

import pytest

from shitposter.clients.text_to_image import OpenAIImageProvider


@pytest.fixture(autouse=True)
def _mock_openai():
    with patch("openai.OpenAI"):
        yield


class TestOpenAIModelValidation:
    @pytest.mark.parametrize("model", ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"])
    def test_allowed_models(self, model):
        provider = OpenAIImageProvider(model=model)
        assert provider.model == model

    def test_default_model(self):
        provider = OpenAIImageProvider()
        assert provider.model == "gpt-image-1-mini"

    @pytest.mark.parametrize("model", ["dall-e-3", "dall-e-2", "sd-xl"])
    def test_rejects_unsupported_model(self, model):
        with pytest.raises(ValueError, match=f"Unsupported model '{model}'"):
            OpenAIImageProvider(model=model)


class TestOpenAISizeValidation:
    @pytest.mark.parametrize(
        "width, height",
        [(1024, 1024), (1536, 1024), (1024, 1536)],
    )
    def test_allowed_sizes(self, width, height):
        provider = OpenAIImageProvider(width=width, height=height)
        assert provider.width == width
        assert provider.height == height

    def test_default_size(self):
        provider = OpenAIImageProvider()
        assert provider.width == 1024
        assert provider.height == 1024

    @pytest.mark.parametrize(
        "width, height",
        [(512, 512), (256, 256), (1920, 1080), (1536, 1536)],
    )
    def test_rejects_unsupported_size(self, width, height):
        with pytest.raises(ValueError, match=f"OpenAI does not support {width}x{height}"):
            OpenAIImageProvider(width=width, height=height)
