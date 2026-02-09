import json

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.config import PromptConfig
from shitposter.steps.base import Step


class ConstructPromptOutput(BaseModel):
    prompt: str


class ConstructPromptStep(Step[PromptConfig, ConstructPromptOutput]):
    def execute(self, ctx: RunContext, input: PromptConfig) -> ConstructPromptOutput:
        output = ConstructPromptOutput(prompt=f"an image of {input.prompt}")
        ctx.prompt = output.prompt
        ctx.prompt_json.write_text(json.dumps(output.model_dump(), indent=2))
        return output
