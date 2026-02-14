import json

from shitposter.clients.text_to_text import TextProvider
from shitposter.steps.base import Step, StepResult


class ConstructPromptStep(Step):
    registry = TextProvider._registry

    def execute(self) -> StepResult:
        template = self.config.get("template")
        text = template.format(**self.inputs) if template else ""
        prompt = self.provider.generate(text)
        self.output = prompt

        metadata = {**self.provider.metadata()}
        artifact = {**metadata, self.name: prompt}
        self.ctx.run_dir.joinpath(f"{self.name}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{prompt!r}")
