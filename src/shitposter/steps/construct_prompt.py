import json

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import TEXT_PROVIDERS
from shitposter.steps.base import ProviderConfig, Step, StepResult


class ConstructPromptStep(Step):
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        cfg = ProviderConfig.model_validate(config)
        provider_cls = TEXT_PROVIDERS[cfg.provider]
        provider = provider_cls(**cfg.model_dump(exclude={"provider"}))
        prompt = provider.generate("")
        ctx.state["prompt"] = prompt

        metadata = {"provider": cfg.provider, "prompt": prompt, **provider.metadata()}
        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps({"prompt": prompt}, indent=2))
        return StepResult(metadata=metadata, summary=f"prompt={prompt!r}")
