import json
import random

from pydantic import BaseModel, field_validator

from shitposter.artifacts import RunContext
from shitposter.steps.base import Step


class PromptInput(BaseModel):
    template: str
    topics: list[str]

    @field_validator("topics")
    @classmethod
    def topics_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("topics must not be empty")
        return v


class PromptOutput(BaseModel):
    prompt: str
    topic: str


class PromptStep(Step[PromptInput, PromptOutput]):
    def execute(self, ctx: RunContext, input: PromptInput) -> PromptOutput:
        topic = random.choice(input.topics)
        prompt = input.template.format(topic=topic)
        output = PromptOutput(prompt=prompt, topic=topic)

        ctx.prompt_txt.write_text(output.prompt)
        ctx.prompt_json.write_text(json.dumps(output.model_dump(), indent=2))

        return output
