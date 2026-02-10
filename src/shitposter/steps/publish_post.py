import json

from shitposter.artifacts import RunContext
from shitposter.clients.publishers import PROVIDERS, TelegramPublisher
from shitposter.steps.base import Step, StepResult


class PublishPostStep(Step):
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        platforms = config.get("platforms", [])

        if not ctx.publish and not ctx.dry_run:
            publisher = TelegramPublisher(debug=True)
            raw = publisher.publish(ctx.state.get("image_path"), ctx.state["caption"])
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
                pub = PROVIDERS[name]()
                if ctx.dry_run:
                    raw = {"result": {}}
                else:
                    raw = pub.publish(ctx.state.get("image_path"), ctx.state["caption"])
                results.append(
                    {
                        "provider": name,
                        "message_id": str(raw.get("result", {}).get("message_id", "")),
                        "metadata": pub.metadata(),
                    }
                )

        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps({"results": results}, indent=2))

        providers = [str(r["provider"]) for r in results]
        if ctx.dry_run:
            summary = "dry run -- skipping publish"
        elif not ctx.publish:
            summary = "published to debug chat"
        else:
            summary = f"published to {', '.join(providers)}"

        return StepResult(
            metadata=[{"provider": r["provider"], "message_id": r["message_id"]} for r in results],
            summary=summary,
        )
