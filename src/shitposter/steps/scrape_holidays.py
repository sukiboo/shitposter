import json
from datetime import date

from shitposter.providers.web_to_context import ContextProvider
from shitposter.steps.base import Step, StepResult


class ScrapeHolidaysStep(Step):
    registry = ContextProvider._registry

    @classmethod
    def validate_config(cls, config: dict) -> None:
        super().validate_config(config)
        val = config.get("date")
        if val is not None:
            if isinstance(val, date):
                pass
            elif isinstance(val, str):
                try:
                    date.fromisoformat(val)
                except ValueError:
                    raise ValueError(f"Invalid date format: {val!r}")
            else:
                raise ValueError(f"'date' must be a string or date, got {type(val).__name__}")

    def _resolve_date(self) -> date:
        val = self.config.get("date")
        if val is None:
            return date.today()
        return val if isinstance(val, date) else date.fromisoformat(str(val))

    def execute(self) -> StepResult:
        target_date = self._resolve_date()
        records = self.provider.generate(target_date)
        entries = self._format(records)
        self.output = entries

        metadata = {**self.provider.metadata(), "date": target_date.isoformat(), **self.inputs}
        artifact = {**metadata, self.name: self.output, "records": records}
        self.artifact_path().write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"scraped {len(entries)} holidays")

    @staticmethod
    def _format(records: list[dict]) -> list[str | None]:
        return [record["name"] for record in records]
