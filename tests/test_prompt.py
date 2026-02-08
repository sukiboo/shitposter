import json

from shitposter.steps.construct_prompt import (
    ConstructPromptInput,
    ConstructPromptOutput,
    ConstructPromptStep,
)


def test_prompt_step_passes_through(run_ctx):
    step = ConstructPromptStep()
    result = step.execute(
        run_ctx,
        ConstructPromptInput(prompt="a cat wearing a business suit"),
    )

    assert isinstance(result, ConstructPromptOutput)
    assert result.prompt == "an image of a cat wearing a business suit"

    saved = json.loads(run_ctx.prompt_json.read_text())
    assert saved["prompt"] == result.prompt
