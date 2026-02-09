import base64
import io
import random
from typing import Any

from PIL import Image


class RandomImageProvider:
    def __init__(self, **kwargs):
        self.width = kwargs.get("width") or 512
        self.height = kwargs.get("height") or 512

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


class OpenAIImageProvider:
    def __init__(self, **kwargs):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = kwargs.get("model") or "gpt-image-1-mini"
        self.width = kwargs.get("width") or 1024
        self.height = kwargs.get("height") or 1024
        self.quality = kwargs.get("quality") or "medium"

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
