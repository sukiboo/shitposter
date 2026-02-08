import json
from pathlib import Path

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_image import RandomImageProvider
from shitposter.steps.base import Step

PROVIDERS = {
    "placeholder": RandomImageProvider,
}


class GenerateImageInput(BaseModel):
    prompt: str
    provider: str = "placeholder"
    width: int = 512
    height: int = 512


class GenerateImageOutput(BaseModel):
    image_path: Path
    provider: str
    metadata: dict


class GenerateImageStep(Step[GenerateImageInput, GenerateImageOutput]):
    def execute(self, ctx: RunContext, input: GenerateImageInput) -> GenerateImageOutput:
        provider_cls = PROVIDERS[input.provider]
        provider = provider_cls()
        image_data = provider.generate(input.prompt, input.width, input.height)

        ctx.image_path.write_bytes(image_data)

        metadata = {"provider": input.provider, "prompt": input.prompt}
        output = GenerateImageOutput(
            image_path=ctx.image_path,
            provider=input.provider,
            metadata=metadata,
        )

        ctx.image_meta_json.write_text(json.dumps(metadata, indent=2))

        return output
