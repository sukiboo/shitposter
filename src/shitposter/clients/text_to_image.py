import base64
import io
import random
from typing import Any

from PIL import Image

from shitposter.clients.base import ImageProvider


class RandomImageProvider(ImageProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        self.width = kwargs.get("width") or 512
        self.height = kwargs.get("height") or 512

    def metadata(self) -> dict:
        return {"width": self.width, "height": self.height, **super().metadata()}

    def generate(self, prompt: str) -> bytes:
        img = Image.new("RGB", (self.width, self.height))
        pixels = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(self.width * self.height)
        ]
        img.putdata(pixels)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


class OpenAIImageProvider(ImageProvider):
    name = "openai"
    ALLOWED_MODELS = {"gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"}
    ALLOWED_SIZES = {(1024, 1024), (1536, 1024), (1024, 1536)}

    def __init__(self, **kwargs):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = kwargs.get("model", "gpt-image-1-mini")
        self.quality = kwargs.get("quality", "medium")
        self.width = kwargs.get("width", 1024)
        self.height = kwargs.get("height", 1024)

        if self.model not in self.ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported model '{self.model}'. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_MODELS))}"
            )
        if (self.width, self.height) not in self.ALLOWED_SIZES:
            raise ValueError(
                f"OpenAI does not support {self.width}x{self.height}. "
                f"Allowed sizes: {', '.join(f'{w}x{h}' for w, h in self.ALLOWED_SIZES)}"
            )

    def metadata(self) -> dict:
        return {
            "model": self.model,
            "quality": self.quality,
            "width": self.width,
            "height": self.height,
            **super().metadata(),
        }

    def generate(self, prompt: str) -> bytes:
        size: Any = f"{self.width}x{self.height}"
        quality: Any = self.quality
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        b64 = response.data[0].b64_json  # type: ignore[index]
        if not b64:
            raise RuntimeError("OpenAI returned no image data")
        return base64.b64decode(b64)
