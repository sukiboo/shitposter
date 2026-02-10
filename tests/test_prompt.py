import json

from shitposter.steps.construct_prompt import ConstructPromptStep


def test_prompt_step_passes_through(run_ctx):
    step = ConstructPromptStep()
    result = step.execute(run_ctx, {"prompt": "a cat wearing a business suit"}, "setup")

    assert result.summary == "prompt='an image of a cat wearing a business suit'"
    assert result.metadata["prompt"] == "an image of a cat wearing a business suit"
    assert run_ctx.state["prompt"] == "an image of a cat wearing a business suit"

    saved = json.loads(run_ctx.run_dir.joinpath("setup.json").read_text())
    assert saved["prompt"] == "an image of a cat wearing a business suit"
