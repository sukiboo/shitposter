import json
from pathlib import Path
from typing import Protocol, Self

from pydantic import BaseModel, model_validator

from shitposter.artifacts import RunContext
from shitposter.steps.base import Step


class Publisher(Protocol):
    def publish(self, image_path: Path | None, caption: str | None) -> dict: ...


class PublishInput(BaseModel):
    image_path: Path | None = None
    caption: str | None = None

    @model_validator(mode="after")
    def at_least_one(self) -> Self:
        if self.image_path is None and self.caption is None:
            raise ValueError("need at least image_path or caption")
        return self


class PublishOutput(BaseModel):
    message_id: str
    platform: str
    raw_response: dict


class PublishStep(Step[PublishInput, PublishOutput]):
    def __init__(self, publisher: Publisher, platform: str):
        self.publisher = publisher
        self.platform = platform

    def execute(self, ctx: RunContext, input: PublishInput) -> PublishOutput:
        raw = self.publisher.publish(input.image_path, input.caption)
        output = PublishOutput(
            message_id=str(raw.get("message_id", raw.get("result", {}).get("message_id", ""))),
            platform=self.platform,
            raw_response=raw,
        )

        ctx.publish_json.write_text(json.dumps(output.model_dump(mode="json"), indent=2))

        return output
