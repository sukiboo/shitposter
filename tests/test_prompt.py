import json

import pytest
from pydantic import ValidationError

from shitposter.steps.prompt import PromptInput, PromptOutput, PromptStep


def test_prompt_step_generates_prompt(run_ctx):
    step = PromptStep()
    result = step.execute(
        run_ctx,
        PromptInput(template="Draw a {topic}", topics=["cat", "dog"]),
    )

    assert isinstance(result, PromptOutput)
    assert result.topic in ("cat", "dog")
    assert result.topic in result.prompt
    assert run_ctx.prompt_txt.read_text() == result.prompt

    saved = json.loads(run_ctx.prompt_json.read_text())
    assert saved["topic"] == result.topic


def test_prompt_input_requires_topics():
    with pytest.raises(ValidationError):
        PromptInput(template="Draw a {topic}", topics=[])
