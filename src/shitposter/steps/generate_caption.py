import json

from shitposter.clients.text_to_text import TextProvider
from shitposter.steps.base import Step, StepResult


class GenerateCaptionStep(Step):
    registry = TextProvider._registry

    def execute(self) -> StepResult:
        input_values = self.inputs
        template = self.config.get("template")
        prompt = template.format(**input_values) if template else list(input_values.values())[0]
        caption = self.provider.generate(prompt)
        self.output = caption

        metadata = {**self.provider.metadata(), "resolved": prompt}
        artifact = {**metadata, self.name: caption}
        self.ctx.run_dir.joinpath(f"{self.name}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{caption!r}")
