import json

from pydantic import BaseModel

from shitposter.artifacts import RunContext
from shitposter.clients.publishers import PROVIDERS, TelegramPublisher
from shitposter.config import PublishConfig
from shitposter.steps.base import Step


class PublishPostInput(BaseModel):
    platforms: list[PublishConfig]


class PublishResult(BaseModel):
    provider: str
    message_id: str
    metadata: dict


class PublishPostOutput(BaseModel):
    results: list[PublishResult]


class PublishPostStep(Step[PublishPostInput, PublishPostOutput]):
    def execute(self, ctx: RunContext, input: PublishPostInput) -> PublishPostOutput:
        if not ctx.publish and not ctx.dry_run:
            publisher = TelegramPublisher(debug=True)
            raw = publisher.publish(ctx.image_path, ctx.caption)
            results = [
                PublishResult(
                    provider="telegram",
                    message_id=str(raw.get("result", {}).get("message_id", "")),
                    metadata=publisher.metadata(),
                )
            ]
        else:
            results = []
            for cfg in input.platforms:
                pub = PROVIDERS[cfg.provider](**cfg.model_dump(exclude={"provider"}))
                if ctx.dry_run:
                    raw = {"result": {}}
                else:
                    raw = pub.publish(ctx.image_path, ctx.caption)
                results.append(
                    PublishResult(
                        provider=cfg.provider,
                        message_id=str(raw.get("result", {}).get("message_id", "")),
                        metadata=pub.metadata(),
                    )
                )

        output = PublishPostOutput(results=results)
        ctx.publish_json.write_text(json.dumps(output.model_dump(mode="json"), indent=2))
        return output
