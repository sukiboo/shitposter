import json
from unittest.mock import patch

from shitposter.steps.choose_holiday import ChooseHolidayStep


def test_placeholder_picks_first(run_ctx):
    entries = ["National Pizza Day", "World Peace Day", "Hug a Cat Day"]
    run_ctx.state["holidays"] = entries

    step = ChooseHolidayStep(
        run_ctx, {"provider": "placeholder", "inputs": ["holidays"]}, "holiday", 1
    )
    result = step.execute()

    assert step.output == "National Pizza Day"
    assert run_ctx.state["holiday"] == "National Pizza Day"

    artifact = json.loads(run_ctx.run_dir.joinpath("1_holiday.json").read_text())
    assert artifact["output"] == "National Pizza Day"
    assert artifact["index"] == 0
    assert result.summary == "chose #0: 'National Pizza Day'"


def test_step_sets_state(run_ctx):
    entries = ["Day A", "Day B", "Day C"]
    run_ctx.state["holidays"] = entries

    with (
        patch(
            "shitposter.providers.text_to_struct.OpenAITextToIntProvider.__init__",
            return_value=None,
        ),
        patch(
            "shitposter.providers.text_to_struct.OpenAITextToIntProvider.generate",
            return_value=2,
        ),
        patch(
            "shitposter.providers.text_to_struct.OpenAITextToIntProvider.metadata",
            return_value={"provider": "openai", "model": "gpt-5-nano"},
        ),
    ):
        step = ChooseHolidayStep(
            run_ctx, {"provider": "openai", "inputs": ["holidays"]}, "holiday", 1
        )
        _ = step.execute()

    assert run_ctx.state["holiday"] == "Day C"
    assert run_ctx.run_dir.joinpath("1_holiday.json").exists()

    artifact = json.loads(run_ctx.run_dir.joinpath("1_holiday.json").read_text())
    assert artifact["index"] == 2
