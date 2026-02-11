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
        holidays = provider.generate()

        ctx.state["holidays"] = holidays
        ctx.state["context"] = self._format(holidays)

        artifact = {"provider": provider_name, "holidays": holidays}
        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps(artifact, indent=2))

        metadata = {"provider": provider_name, "count": len(holidays), **provider.metadata()}
        return StepResult(metadata=metadata, summary=f"{len(holidays)} holidays")

    @staticmethod
    def _format(holidays: list[dict]) -> str:
        if not holidays:
            return "No holidays today."
        lines = ["Today's holidays:"]
        lines.extend(f"- {h['name']}" for h in holidays)
        return "\n".join(lines)
