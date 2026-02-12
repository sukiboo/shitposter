import json

from shitposter.steps.construct_prompt import ConstructPromptStep


def test_prompt_step_passes_through(run_ctx):
    step = ConstructPromptStep()
    result = step.execute(run_ctx, {"provider": "placeholder"}, "setup")

    assert result.summary == "prompt='Placeholder text'"
    assert result.metadata["prompt"] == "Placeholder text"
    assert run_ctx.state["prompt"] == "Placeholder text"

    saved = json.loads(run_ctx.run_dir.joinpath("setup.json").read_text())
    assert saved["prompt"] == "Placeholder text"


def test_prompt_step_fixed_string(run_ctx):
    step = ConstructPromptStep()
    result = step.execute(
        run_ctx, {"provider": "constant", "prompt": "a cat wearing a business suit"}, "setup"
    )

    assert result.summary == "prompt='a cat wearing a business suit'"
    assert result.metadata["prompt"] == "a cat wearing a business suit"
    assert run_ctx.state["prompt"] == "a cat wearing a business suit"

    saved = json.loads(run_ctx.run_dir.joinpath("setup.json").read_text())
    assert saved["prompt"] == "a cat wearing a business suit"
