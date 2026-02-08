import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.steps.base import Step


class ImageProvider(Protocol):
    def generate(self, prompt: str, output_path: Path, width: int, height: int) -> dict: ...


class RandomImageProvider:
    def generate(self, prompt: str, output_path: Path, width: int, height: int) -> dict:
        import random as _random

        from PIL import Image

        img = Image.new("RGB", (width, height))
        pixels = [
            (_random.randint(0, 255), _random.randint(0, 255), _random.randint(0, 255))
            for _ in range(width * height)
        ]
        img.putdata(pixels)
        img.save(output_path)
        return {"provider": "placeholder", "prompt": prompt}


PROVIDERS: dict[str, type[ImageProvider]] = {
    "placeholder": RandomImageProvider,
}


class ImageInput(BaseModel):
    prompt: str
    provider: str = "placeholder"
    width: int = 1024
    height: int = 1024


class ImageOutput(BaseModel):
    image_path: Path
    provider: str
    metadata: dict


class ImageStep(Step[ImageInput, ImageOutput]):
    def execute(self, ctx: RunContext, input: ImageInput) -> ImageOutput:
        provider_cls = PROVIDERS[input.provider]
        provider = provider_cls()
        metadata = provider.generate(input.prompt, ctx.image_path, input.width, input.height)

        output = ImageOutput(
            image_path=ctx.image_path,
            provider=input.provider,
            metadata=metadata,
        )

        ctx.image_meta_json.write_text(json.dumps(output.metadata, indent=2))

        return output
