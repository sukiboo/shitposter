from pydantic import BaseModel

from shitposter.artifacts import RunContext
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
        caption = input.template.format(
            topic=input.topic,
            prompt=input.prompt,
        )
        output = CaptionOutput(caption=caption)

        ctx.caption_txt.write_text(output.caption)

        return output
