from shitposter.providers.publishers import PublishingProvider, TelegramPublisher
from shitposter.steps.base import Step, StepResult


class PublishPostStep(Step):
    @classmethod
    def validate_config(cls, config: dict) -> None:
        super().validate_config(config)
        platforms = config.get("platforms")
        if not platforms:
            raise ValueError("publish_post requires 'platforms'")
        for p in platforms:
            if p not in PublishingProvider._registry:
                raise ValueError(
                    f"Unknown publisher '{p}'. Allowed: {sorted(PublishingProvider._registry)}"
                )

    def execute(self) -> StepResult:
        platforms = self.config.get("platforms", [])
        input_list = list(self.inputs.values())
        image_path = input_list[0] if input_list else None
        caption = input_list[1] if len(input_list) > 1 else ""

        if not self.ctx.publish and not self.ctx.dry_run:
            publisher = TelegramPublisher(debug=True)
            raw = publisher.publish(image_path, caption)
            results = [
                {
                    "provider": "telegram",
                    "message_id": str(raw.get("result", {}).get("message_id", "")),
                    "metadata": publisher.metadata(),
                }
            ]
        else:
            results = []
            for name in platforms:
                pub = PublishingProvider._registry[name]()
                if self.ctx.dry_run:
                    raw = {"result": {}}
                else:
                    raw = pub.publish(image_path, caption)
                results.append(
                    {
                        "provider": name,
                        "message_id": str(raw.get("result", {}).get("message_id", "")),
                        "metadata": pub.metadata(),
                    }
                )

        providers = [str(r["provider"]) for r in results]
        if self.ctx.dry_run:
            summary = "dry run -- skipping publish"
        elif not self.ctx.publish:
            summary = "published to debug chat"
        else:
            summary = f"published to {', '.join(providers)}"
        metadata = [{"provider": r["provider"], "message_id": r["message_id"]} for r in results]
        self.write_artifact(results)

        return StepResult(metadata=metadata, summary=summary)
