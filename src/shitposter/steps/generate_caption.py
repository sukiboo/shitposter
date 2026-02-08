import json

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import PlaceholderCaptionProvider
from shitposter.steps.base import Step

PROVIDERS = {
    "placeholder": PlaceholderCaptionProvider,
}


class GenerateCaptionInput(BaseModel):
    prompt: str
    provider: str


class GenerateCaptionOutput(BaseModel):
    caption_text: str


class GenerateCaptionStep(Step[GenerateCaptionInput, GenerateCaptionOutput]):
    def execute(self, ctx: RunContext, input: GenerateCaptionInput) -> GenerateCaptionOutput:
        provider_cls = PROVIDERS[input.provider]
        provider = provider_cls()
        caption_text = provider.generate(input.prompt)
        output = GenerateCaptionOutput(caption_text=caption_text)
        ctx.caption_json.write_text(json.dumps(output.model_dump(), indent=2))
        return output
