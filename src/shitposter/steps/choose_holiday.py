from shitposter.providers.text_to_int import TextToIntProvider
from shitposter.steps.base import Step, StepResult


class ChooseHolidayStep(Step):
    registry = TextToIntProvider._registry

    def execute(self) -> StepResult:
        input_names = self.config.get("inputs", [])
        if not input_names:
            raise ValueError("choose_holiday requires a candidate-list input")

        # The first input is the selectable list; any remaining inputs provide
        # context to the prompt, such as recently selected holidays.
        entries = self.inputs[input_names[0]]
        if not isinstance(entries, list):
            raise TypeError("choose_holiday's first input must be a list")

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
