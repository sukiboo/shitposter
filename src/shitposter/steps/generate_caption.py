from typing import Protocol

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import PlaceholderCaptionProvider
from shitposter.steps.base import Step


class CaptionProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


PROVIDERS: dict[str, type[CaptionProvider]] = {
    "placeholder": PlaceholderCaptionProvider,
}


class GenerateCaptionInput(BaseModel):
    prompt: str
    provider: str


class GenerateCaptionOutput(BaseModel):
    caption: str


class GenerateCaptionStep(Step[GenerateCaptionInput, GenerateCaptionOutput]):
    def execute(self, ctx: RunContext, input: GenerateCaptionInput) -> GenerateCaptionOutput:
        provider_cls = PROVIDERS[input.provider]
        provider = provider_cls()
        caption = provider.generate(input.prompt)
        output = GenerateCaptionOutput(caption=caption)

        ctx.caption_txt.write_text(output.caption)

        return output
