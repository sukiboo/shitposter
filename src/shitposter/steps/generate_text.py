from shitposter.providers.text_to_caption import TextToCaptionProvider
from shitposter.providers.text_to_text import TextProvider
from shitposter.steps.base import Step, StepResult


class GenerateTextStep(Step):
    registry = TextProvider._registry

    def execute(self) -> StepResult:
        if "prompt" in self.config:
            self.inputs["prompt"] = self.config["prompt"]
        prompt = self.template.format(**self.inputs)
        self.output = self.provider.generate(prompt)

        artifact = {**self.metadata, "prompt": prompt}
        self.write_artifact(artifact)

        return StepResult(metadata=self.metadata, summary=f"{self.output!r}")


class GenerateCaptionStep(GenerateTextStep):
    registry = TextToCaptionProvider._registry  # type: ignore[assignment]
