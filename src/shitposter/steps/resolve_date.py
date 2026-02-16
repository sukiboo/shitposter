from shitposter.providers.text_to_date import DateProvider
from shitposter.steps.base import Step, StepResult


class ResolveDateStep(Step):
    registry = DateProvider._registry

    def execute(self) -> StepResult:
        self.inputs["value"] = self.config.get("value")
        self.output = self.provider.generate()
        self.write_artifact(self.metadata)
        return StepResult(metadata=self.metadata, summary=str(self.output))
