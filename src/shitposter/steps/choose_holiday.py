from shitposter.providers.text_to_struct import TextToIntProvider
from shitposter.steps.base import Step, StepResult


class ChooseHolidayStep(Step):
    registry = TextToIntProvider._registry
    default_prompt = "Pick one of the following entries:"

    def execute(self) -> StepResult:
        entries = list(self.inputs.values())[0]
        prompt = self.template.format(**self.inputs) or self.default_prompt
        index = self.provider.generate(prompt, entries)
        self.output = entries[index]

        artifact = {
            **self.metadata,
            "index": index,
            "prompt": prompt,
        }
        self.write_artifact(artifact)

        return StepResult(metadata=self.metadata, summary=f"chose #{index}: '{self.output}'")
