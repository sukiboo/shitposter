import json

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_text import TEXT_PROVIDERS
from shitposter.steps.base import Step, StepResult, setup_provider


class GenerateCaptionStep(Step):
    @classmethod
    def validate_config(cls, config: dict) -> None:
        if "provider" not in config:
            raise ValueError("generate_caption requires 'provider'")
        if config["provider"] not in TEXT_PROVIDERS:
            raise ValueError(
                f"Unknown text provider '{config['provider']}'. "
                f"Allowed: {sorted(TEXT_PROVIDERS)}"
            )

    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        provider_name, provider = setup_provider(TEXT_PROVIDERS, config)

        template = config.get("template")
        prompt = template.format(**ctx.state) if template else ctx.state["prompt"]
        caption = provider.generate(prompt)

        ctx.state["caption"] = caption
        metadata = {"provider": provider_name, "prompt": prompt, **provider.metadata()}
        ctx.run_dir.joinpath(f"{key}.json").write_text(
            json.dumps({"caption_text": caption, "metadata": metadata}, indent=2)
        )

        return StepResult(metadata=metadata, summary=f"caption={caption!r}")
