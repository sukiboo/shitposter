import json

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import TEXT_PROVIDERS
from shitposter.steps.base import ProviderConfig, Step, StepResult


class GenerateCaptionStep(Step):
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        cfg = ProviderConfig.model_validate(config)
        provider_cls = TEXT_PROVIDERS[cfg.provider]
        provider = provider_cls(**cfg.model_dump(exclude={"provider"}))
        caption_text = provider.generate(ctx.state["prompt"])
        ctx.state["caption"] = caption_text

        metadata = {"provider": cfg.provider, "prompt": ctx.state["prompt"], **provider.metadata()}
        ctx.run_dir.joinpath(f"{key}.json").write_text(
            json.dumps({"caption_text": caption_text, "metadata": metadata}, indent=2)
        )
        return StepResult(metadata=metadata, summary=f"caption={caption_text!r}")
