from shitposter.providers.text_to_int import TextToIntProvider
from shitposter.steps.base import Step, StepResult


class ChooseHolidayStep(Step):
    registry = TextToIntProvider._registry

    def execute(self) -> StepResult:
        (entries,) = self.inputs.values()
        prompt = self.template.format(**self.inputs)
        index = self.provider.generate(prompt, entries)
        self.output = entries[index]

        artifact = {
            **self.metadata,
            "index": index,
            "prompt": prompt,
        }
        self.write_artifact(artifact)

        return StepResult(metadata=self.metadata, summary=f"chose #{index}: '{self.output}'")
