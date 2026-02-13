import json
from datetime import date

from shitposter.clients.web_to_context import CONTEXT_PROVIDERS
from shitposter.steps.base import Step, StepResult


class CollectContextStep(Step):
    registry = CONTEXT_PROVIDERS

    @classmethod
    def validate_config(cls, config: dict) -> None:
        super().validate_config(config)
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

    def execute(self) -> StepResult:
        records = self.provider.generate()
        entries = self._format(records)
        self.output = entries

        metadata = {"provider": self.provider_name, **self.provider.metadata(), **self.inputs}
        artifact = {**metadata, self.name: self.output, "records": records}
        self.ctx.run_dir.joinpath(f"{self.name}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"retrieved {len(entries)} holidays")

    @staticmethod
    def _format(records: list[dict]) -> list[str | None]:
        return [record["name"] for record in records]
