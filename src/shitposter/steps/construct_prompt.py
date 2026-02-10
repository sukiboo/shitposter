import json

from shitposter.artifacts import RunContext
from shitposter.steps.base import Step, StepResult


class ConstructPromptStep(Step):
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        prompt = f"an image of {config['prompt']}"
        ctx.state["prompt"] = prompt
        ctx.run_dir.joinpath(f"{key}.json").write_text(json.dumps({"prompt": prompt}, indent=2))
        return StepResult(metadata={"prompt": prompt}, summary=f"prompt={prompt!r}")
