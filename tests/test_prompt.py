import json

from shitposter.steps.generate_text import GenerateTextStep


def test_prompt_step_passes_through(run_ctx):
    result = GenerateTextStep(run_ctx, {"provider": "placeholder"}, "setup", 0).execute()

    assert result.summary == "'Placeholder text'"
    assert run_ctx.state["setup"] == "Placeholder text"

    saved = json.loads(run_ctx.run_dir.joinpath("0_setup.json").read_text())
    assert saved["output"] == "Placeholder text"


def test_prompt_step_fixed_string(run_ctx):
    result = GenerateTextStep(
        run_ctx, {"provider": "constant", "prompt": "a cat wearing a business suit"}, "setup", 0
    ).execute()

    assert result.summary == "'a cat wearing a business suit'"
    assert run_ctx.state["setup"] == "a cat wearing a business suit"

    saved = json.loads(run_ctx.run_dir.joinpath("0_setup.json").read_text())
    assert saved["output"] == "a cat wearing a business suit"
