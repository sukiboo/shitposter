import json

from shitposter.clients.text_to_image import IMAGE_PROVIDERS
from shitposter.steps.base import Step, StepResult


class GenerateImageStep(Step):
    registry = IMAGE_PROVIDERS

    def execute(self) -> StepResult:
        input_values = self.inputs
        template = self.config.get("template")
        prompt = template.format(**input_values) if template else list(input_values.values())[0]
        image_data = self.provider.generate(prompt)

        image_path = self.ctx.run_dir.joinpath(f"{self.name}.png")
        image_path.write_bytes(image_data)
        self.output = str(image_path)

        metadata = {"provider": self.provider_name, **self.provider.metadata(), "resolved": prompt}
        artifact = {**metadata, self.name: self.output}
        self.ctx.run_dir.joinpath(f"{self.name}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"{image_path}")
