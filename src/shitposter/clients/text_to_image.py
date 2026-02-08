import io
import random

from PIL import Image


class RandomImageProvider:
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
