from shitposter.providers.text_to_struct import TextToCaptionProvider
from shitposter.steps.base import Step, StepResult


class GenerateCaptionStep(Step):
    registry = TextToCaptionProvider._registry

    def execute(self) -> StepResult:
        prompt = self.template.format(**self.inputs)
        self.output = self.provider.generate(prompt)

        metadata = {**self.provider.metadata(), **self.inputs, "prompt": prompt}
        artifact = {**metadata, self.name: self.output}
        self.write_artifact(artifact)

        return StepResult(metadata=metadata, summary=f"{self.output!r}")
