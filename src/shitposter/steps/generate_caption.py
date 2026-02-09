import json

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import PROVIDERS
from shitposter.config import CaptionConfig
from shitposter.steps.base import Step


class GenerateCaptionOutput(BaseModel):
    caption_text: str
    metadata: dict


class GenerateCaptionStep(Step[CaptionConfig, GenerateCaptionOutput]):
    def execute(self, ctx: RunContext, input: CaptionConfig) -> GenerateCaptionOutput:
        provider_cls = PROVIDERS[input.provider]
        provider = provider_cls(**input.model_dump(exclude={"provider"}))
        caption_text = provider.generate(ctx.prompt)
        ctx.caption = caption_text

        metadata = {"provider": input.provider, "prompt": ctx.prompt, **provider.metadata()}
        output = GenerateCaptionOutput(caption_text=caption_text, metadata=metadata)
        ctx.caption_json.write_text(json.dumps(output.model_dump(), indent=2))

        return output
