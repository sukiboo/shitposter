import json

from shitposter.clients.text_to_int import TEXT_TO_INT_PROVIDERS
from shitposter.steps.base import Step, StepResult


class ChooseEntryStep(Step):
    registry = TEXT_TO_INT_PROVIDERS

    def execute(self) -> StepResult:
        entries_key, entries = list(self.inputs.items())[0]
        template = self.config.get("template", "Pick one of the following entries:")
        prompt = template.format(**self.inputs)
        index = self.provider.generate(prompt, entries)
        self.output = entries[index]

        metadata = {"provider": self.provider_name, **self.provider.metadata(), **self.inputs}
        artifact = {
            **metadata,
            self.name: self.output,
            "prompt": prompt,
            entries_key: entries,
            "index": index,
        }
        self.ctx.run_dir.joinpath(f"{self.name}.json").write_text(json.dumps(artifact, indent=2))

        return StepResult(metadata=metadata, summary=f"chose #{index}: '{entries[index]}'")
