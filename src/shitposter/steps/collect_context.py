import json
from datetime import date

from shitposter.artifacts import RunContext
from shitposter.clients.web_to_context import CONTEXT_PROVIDERS
from shitposter.steps.base import Step, StepResult, setup_provider


class CollectContextStep(Step):
    @classmethod
    def validate_config(cls, config: dict) -> None:
        if "provider" not in config:
            raise ValueError("collect_context requires 'provider'")
        if config["provider"] not in CONTEXT_PROVIDERS:
            raise ValueError(
                f"Unknown context provider '{config['provider']}'. "
                f"Allowed: {sorted(CONTEXT_PROVIDERS)}"
            )
        if "date" in config:
            val = config["date"]
            if isinstance(val, date):
                pass
            elif isinstance(val, str):
                try:
                    date.fromisoformat(val)
                except ValueError:
                    raise ValueError(f"Invalid date format: {val!r}")
            else:
                raise ValueError(f"'date' must be a string or date, got {type(val).__name__}")

    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        provider_name, provider = setup_provider(CONTEXT_PROVIDERS, config)

        records = provider.generate()
        holidays = self._format(records)

        metadata = {"provider": provider_name, **provider.metadata(), "count": len(holidays)}
        ctx.state["holidays"] = holidays
        artifact = {**metadata, "holidays": holidays, "records": records}
        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{len(holidays)} holidays")

    @staticmethod
    def _format(records: list[dict]) -> list[str | None]:
        return [record["name"] for record in records]
