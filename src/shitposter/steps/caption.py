from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import TemplateCaptionProvider
from shitposter.steps.base import Step


class CaptionInput(BaseModel):
    prompt: str
    topic: str
    template: str
    image_metadata: dict | None = None


class CaptionOutput(BaseModel):
    caption: str


class CaptionStep(Step[CaptionInput, CaptionOutput]):
    def execute(self, ctx: RunContext, input: CaptionInput) -> CaptionOutput:
        provider = TemplateCaptionProvider()
        caption = provider.generate(input.template, input.topic, input.prompt)
        output = CaptionOutput(caption=caption)

        ctx.caption_txt.write_text(output.caption)

        return output
