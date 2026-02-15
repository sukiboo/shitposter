import json
from datetime import date

from shitposter.providers.text_to_struct import TextToEmojiProvider
from shitposter.steps.base import Step, StepResult


class ConstructHeaderStep(Step):
    registry = TextToEmojiProvider._registry

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
        prompt = self.template.format(**self.inputs)
        emojis = self.provider.generate(prompt)
        header = f"{target_date:%b %-d} \u2014 {self.inputs['holiday']} {emojis}"
        self.output = header

        metadata = {**self.provider.metadata(), "date": target_date.isoformat(), **self.inputs}
        artifact = {**metadata, self.name: self.output, "prompt": prompt}
        self.artifact_path().write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{self.output!r}")
