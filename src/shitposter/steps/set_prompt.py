import json

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import TEXT_PROVIDERS
from shitposter.steps.base import Step, StepResult, setup_provider


class SetPromptStep(Step):
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        if prompt := config.get("prompt"):
            metadata = {"prompt": prompt}
        else:
            provider_name, provider = setup_provider(TEXT_PROVIDERS, config)

            prompt = provider.generate("")
            metadata = {"provider": provider_name, "prompt": prompt, **provider.metadata()}

        ctx.state["prompt"] = prompt
        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps({"prompt": prompt}, indent=2))

        return StepResult(metadata=metadata, summary=f"prompt={prompt!r}")
