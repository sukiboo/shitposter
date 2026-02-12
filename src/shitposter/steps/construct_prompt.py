import json

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import TEXT_PROVIDERS
from shitposter.steps.base import Step, StepResult, setup_provider


class ConstructPromptStep(Step):
    @classmethod
    def validate_config(cls, config: dict) -> None:
        if "provider" not in config:
            raise ValueError("construct_prompt requires 'provider'")
        if config["provider"] not in TEXT_PROVIDERS:
            raise ValueError(
                f"Unknown text provider '{config['provider']}'. "
                f"Allowed: {sorted(TEXT_PROVIDERS)}"
            )

    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        provider_name, provider = setup_provider(TEXT_PROVIDERS, config)

        prompt = provider.generate(config.get("prompt", ""))

        metadata = {"provider": provider_name, **provider.metadata()}
        ctx.state["prompt"] = prompt
        artifact = {**metadata, "prompt": prompt}
        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{prompt!r}")
