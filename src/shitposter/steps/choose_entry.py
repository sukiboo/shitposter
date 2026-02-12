import json

from shitposter.artifacts import RunContext
from shitposter.clients.text_to_int import TEXT_TO_INT_PROVIDERS
from shitposter.steps.base import Step, StepResult, setup_provider


class ChooseEntryStep(Step):
    @classmethod
    def validate_config(cls, config: dict) -> None:
        if "provider" not in config:
            raise ValueError("choose_entry requires 'provider'")
        if config["provider"] not in TEXT_TO_INT_PROVIDERS:
            raise ValueError(
                f"Unknown text_to_int provider '{config['provider']}'. "
                f"Allowed: {sorted(TEXT_TO_INT_PROVIDERS)}"
            )
        if "entries_key" not in config:
            raise ValueError("choose_entry requires 'entries_key'")

    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        provider_name, provider = setup_provider(TEXT_TO_INT_PROVIDERS, config)

        entries = ctx.state[config["entries_key"]]
        template = config.get("template", "Pick one of the following entries:")
        prompt = template.format(**ctx.state)
        index = provider.generate(prompt, entries)
        ctx.state[key] = entries[index]

        metadata = {"provider": provider_name, **provider.metadata(), "index": index}
        artifact = {**metadata, "entry": entries[index], "prompt": prompt, "entries": entries}
        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"chose #{index}: '{entries[index]}'")
