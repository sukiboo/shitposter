import json
from pathlib import Path

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_image import OpenAIImageProvider, RandomImageProvider
from shitposter.config import ImageConfig
from shitposter.steps.base import Step

PROVIDERS: dict[str, type[RandomImageProvider | OpenAIImageProvider]] = {
    "placeholder": RandomImageProvider,
    "openai": OpenAIImageProvider,
}


class GenerateImageOutput(BaseModel):
    image_path: Path
    provider: str
    metadata: dict


class GenerateImageStep(Step[ImageConfig, GenerateImageOutput]):
    def execute(self, ctx: RunContext, input: ImageConfig) -> GenerateImageOutput:
        provider_cls = PROVIDERS[input.provider]
        provider = provider_cls(**input.model_dump(exclude={"provider"}))
        image_data = provider.generate(ctx.prompt)

        ctx.image_path.write_bytes(image_data)

        metadata = {"provider": input.provider, "prompt": ctx.prompt}
        output = GenerateImageOutput(
            image_path=ctx.image_path,
            provider=input.provider,
            metadata=metadata,
        )

        ctx.image_meta_json.write_text(json.dumps(metadata, indent=2))

        return output
