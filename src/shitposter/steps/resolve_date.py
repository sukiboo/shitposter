from datetime import date

from shitposter.steps.base import Step, StepResult


class ResolveDateStep(Step):
    registry = None

    @classmethod
    def validate_config(cls, config: dict) -> None:
        val = config.get("value")
        if val is not None:
            if isinstance(val, date):
                pass
            elif isinstance(val, str):
                try:
                    date.fromisoformat(val)
                except ValueError:
                    raise ValueError(f"Invalid date format: {val!r}")
            else:
                raise ValueError(f"'value' must be a string or date, got {type(val).__name__}")

    def execute(self) -> StepResult:
        val = self.config.get("value")
        if val is None:
            self.output = date.today()
        elif isinstance(val, date):
            self.output = val
        else:
            self.output = date.fromisoformat(str(val))

        metadata = {"input": val}
        artifact = {self.name: self.output}
        self.write_artifact(artifact)

        return StepResult(metadata=metadata, summary=self.output.isoformat())
