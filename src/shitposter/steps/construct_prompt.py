import json

from shitposter.providers.text_to_text import TextProvider
from shitposter.steps.base import Step, StepResult


class ConstructPromptStep(Step):
    registry = TextProvider._registry

    def execute(self) -> StepResult:
        prompt = self.template.format(**self.inputs)
        self.output = self.provider.generate(prompt)

        metadata = {**self.provider.metadata(), **self.inputs}
        artifact = {**metadata, self.name: self.output, "prompt": prompt}
        self.artifact_path().write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{self.output!r}")
