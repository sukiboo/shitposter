import json

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.telegram import TelegramClient
from shitposter.config import PublishConfig
from shitposter.steps.base import Step


class PublishPostOutput(BaseModel):
    message_id: str
    platform: str
    raw_response: dict


class PublishPostStep(Step[PublishConfig, PublishPostOutput]):
    def execute(self, ctx: RunContext, input: PublishConfig) -> PublishPostOutput:
        if ctx.dry_run:
            return PublishPostOutput(message_id="", platform=input.platform, raw_response={})

        assert ctx.env is not None

        if ctx.publish:
            bot_token = ctx.env.telegram_channel_bot_token
            chat_id = ctx.env.telegram_channel_chat_id
        else:
            bot_token = ctx.env.telegram_debug_bot_token
            chat_id = ctx.env.telegram_debug_chat_id

        publisher = TelegramClient(bot_token=bot_token, chat_id=chat_id)
        raw = publisher.publish(ctx.image_path, ctx.caption)
        output = PublishPostOutput(
            message_id=str(raw.get("message_id", raw.get("result", {}).get("message_id", ""))),
            platform=input.platform,
            raw_response=raw,
        )

        ctx.publish_json.write_text(json.dumps(output.model_dump(mode="json"), indent=2))

        return output
