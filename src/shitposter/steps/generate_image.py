import json

from shitposter.providers.text_to_image import ImageProvider
from shitposter.steps.base import Step, StepResult


class GenerateImageStep(Step):
    registry = ImageProvider._registry

    def execute(self) -> StepResult:
        prompt = self.template.format(**self.inputs)
        image_data = self.provider.generate(prompt)

        image_path = self.ctx.run_dir.joinpath(f"{self.name}.png")
        image_path.write_bytes(image_data)
        self.output = str(image_path)

        metadata = {**self.provider.metadata(), **self.inputs, "prompt": prompt}
        artifact = {**metadata, self.name: self.output}
        self.artifact_path().write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{self.output}")
