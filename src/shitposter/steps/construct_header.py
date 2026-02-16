from shitposter.providers.text_to_struct import TextToEmojiProvider
from shitposter.steps.base import Step, StepResult


class ConstructHeaderStep(Step):
    registry = TextToEmojiProvider._registry

    def execute(self) -> StepResult:
        prompt = self.template.format(**self.inputs)
        emojis = self.provider.generate(prompt)
        header = f"{self.inputs['date']:%B %-d} \u2014 {self.inputs['holiday']} {emojis}"
        self.output = header

        artifact = {**self.metadata, "prompt": prompt}
        self.write_artifact(artifact)

        return StepResult(metadata=self.metadata, summary=f"{self.output!r}")
