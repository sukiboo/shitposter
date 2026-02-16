from shitposter.providers.publishers import PublishingProvider
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

        results = []
        for name in platforms:
            pub = PublishingProvider._registry[name]()
            if self.ctx.dry_run:
                raw: dict = {"result": {}}
            else:
                raw = pub.safe_publish(self.inputs.get("image"), self.inputs.get("caption", ""))
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
        else:
            summary = f"published to {', '.join(providers)}"
        metadata = [{"provider": r["provider"], "message_id": r["message_id"]} for r in results]
        artifact = {**self.inputs, "result": results}
        self.write_artifact(artifact)

        return StepResult(metadata=metadata, summary=summary)
