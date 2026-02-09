import json

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import (
    OpenAICaptionProvider,
    PlaceholderCaptionProvider,
)
from shitposter.config import CaptionConfig
from shitposter.steps.base import Step

PROVIDERS = {
    "placeholder": PlaceholderCaptionProvider,
    "openai": OpenAICaptionProvider,
}


class GenerateCaptionOutput(BaseModel):
    caption_text: str


class GenerateCaptionStep(Step[CaptionConfig, GenerateCaptionOutput]):
    def execute(self, ctx: RunContext, input: CaptionConfig) -> GenerateCaptionOutput:
        provider_cls = PROVIDERS[input.provider]
        provider = provider_cls(model=input.model)
        caption_text = provider.generate(ctx.prompt)
        ctx.caption = caption_text
        output = GenerateCaptionOutput(caption_text=caption_text)
        ctx.caption_json.write_text(json.dumps(output.model_dump(), indent=2))
        return output
