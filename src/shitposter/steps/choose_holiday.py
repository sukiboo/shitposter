from shitposter.providers.text_to_int import TextToIntProvider
from shitposter.steps.base import Step, StepResult


class ChooseHolidayStep(Step):
    registry = TextToIntProvider._registry

    def execute(self) -> StepResult:
        input_names = self.config.get("inputs", [])
        if not input_names:
            raise ValueError("choose_holiday requires a candidate-list input")

        # The first input maps the selectable entries to their descriptions; any
        # remaining inputs feed the prompt (selection rules) and the context
        # (background such as recently selected holidays).
        entries = self.inputs[input_names[0]]
        if not isinstance(entries, dict):
            raise TypeError("choose_holiday's first input must be a dict of entry: description")

        prompt = self.template.format(**self.inputs)
        context = self.config.get("context", "").format(**self.inputs)
        index = self.provider.generate(prompt, entries, context)
        self.output = list(entries)[index]

        artifact = {
            **self.metadata,
            "index": index,
            "prompt": prompt,
            "context": context,
        }
        self.write_artifact(artifact)

        return StepResult(metadata=self.metadata, summary=f"chose #{index}: '{self.output}'")
