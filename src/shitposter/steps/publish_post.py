import json
from pathlib import Path

from pydantic import BaseModel, model_validator

from shitposter.artifacts import RunContext
from shitposter.clients.telegram import TelegramClient
from shitposter.config import EnvSettings
from shitposter.steps.base import Step


class PublishPostInput(BaseModel):
    image_path: Path | None = None
    caption: str | None = None

    @model_validator(mode="after")
    def at_least_one(self) -> "PublishPostInput":
        if self.image_path is None and self.caption is None:
            raise ValueError("need at least `image_path` or `caption`")
        return self


class PublishPostOutput(BaseModel):
    message_id: str
    platform: str
    raw_response: dict


class PublishPostStep(Step[PublishPostInput, PublishPostOutput]):
    def __init__(self, env: EnvSettings, platform: str, publish: bool):
        self.env = env
        self.platform = platform
        self.publish = publish

    def execute(self, ctx: RunContext, input: PublishPostInput) -> PublishPostOutput:
        if ctx.dry_run:
            return PublishPostOutput(message_id="", platform=self.platform, raw_response={})

        if self.publish:
            bot_token = self.env.telegram_channel_bot_token
            chat_id = self.env.telegram_channel_chat_id
        else:
            bot_token = self.env.telegram_debug_bot_token
            chat_id = self.env.telegram_debug_chat_id

        publisher = TelegramClient(bot_token=bot_token, chat_id=chat_id)
        raw = publisher.publish(input.image_path, input.caption)
        output = PublishPostOutput(
            message_id=str(raw.get("message_id", raw.get("result", {}).get("message_id", ""))),
            platform=self.platform,
            raw_response=raw,
        )

        ctx.publish_json.write_text(json.dumps(output.model_dump(mode="json"), indent=2))

        return output
