import json

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.steps.base import Step


class ConstructPromptInput(BaseModel):
    prompt: str


class ConstructPromptOutput(BaseModel):
    prompt: str


class ConstructPromptStep(Step[ConstructPromptInput, ConstructPromptOutput]):
    def execute(self, ctx: RunContext, input: ConstructPromptInput) -> ConstructPromptOutput:
        output = ConstructPromptOutput(prompt=input.prompt)

        ctx.prompt_txt.write_text(output.prompt)
        ctx.prompt_json.write_text(json.dumps(output.model_dump(), indent=2))

        return output
