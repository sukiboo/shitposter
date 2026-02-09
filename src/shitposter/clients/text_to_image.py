import base64
import io
import random
from typing import Any

from PIL import Image


class RandomImageProvider:
    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str, width: int, height: int) -> bytes:
        img = Image.new("RGB", (width, height))
        pixels = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(width * height)
        ]
        img.putdata(pixels)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


class OpenAIImageProvider:
    def __init__(self, model: str = "dall-e-3", **kwargs):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model

    def generate(self, prompt: str, width: int, height: int) -> bytes:
        size: Any = f"{width}x{height}"
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            response_format="b64_json",
            n=1,
        )
        b64 = response.data[0].b64_json
        if not b64:
            raise RuntimeError("OpenAI returned no image data")
        return base64.b64decode(b64)
