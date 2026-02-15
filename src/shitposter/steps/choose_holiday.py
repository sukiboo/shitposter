import json

from shitposter.providers.text_to_struct import TextToIntProvider
from shitposter.steps.base import Step, StepResult


class ChooseHolidayStep(Step):
    registry = TextToIntProvider._registry
    default_prompt = "Pick one of the following entries:"

    def execute(self) -> StepResult:
        entries = list(self.inputs.values())[0]
        prompt = (self.template or self.default_prompt).format(**self.inputs)
        index = self.provider.generate(prompt, entries)
        self.output = entries[index]

        metadata = {**self.provider.metadata(), **self.inputs}
        artifact = {
            **metadata,
            self.name: self.output,
            "prompt": prompt,
            "index": index,
        }
        self.artifact_path().write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"chose #{index}: '{self.output}'")
