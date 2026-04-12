import json
from unittest.mock import patch

from shitposter.steps.select_emojis import SelectEmojisStep


def test_placeholder_returns_party_popper(run_ctx):
    run_ctx.state["holiday"] = "National Pizza Day"

    step = SelectEmojisStep(
        run_ctx,
        {"provider": "placeholder", "inputs": ["holiday"], "template": "emoji for {holiday}"},
        "header_emojis",
        1,
    )
    result = step.execute()

    assert step.output == "\U0001f389"
    assert run_ctx.state["header_emojis"] == "\U0001f389"
    assert result.summary == "'\U0001f389'"


def test_template_rendered_before_provider_call(run_ctx):
    run_ctx.state["holiday"] = "Halloween"

    with (
        patch(
            "shitposter.providers.text_to_emoji.OpenAITextToEmojiProvider.__init__",
            return_value=None,
        ),
        patch(
            "shitposter.providers.text_to_emoji.OpenAITextToEmojiProvider.generate",
            return_value="\U0001f383\U0001f47b",
        ) as mock_generate,
        patch(
            "shitposter.providers.text_to_emoji.OpenAITextToEmojiProvider.metadata",
            return_value={"provider": "openai", "model": "gpt-5-mini"},
        ),
    ):
        step = SelectEmojisStep(
            run_ctx,
            {
                "provider": "openai",
                "inputs": ["holiday"],
                "template": "Pick emojis for: {holiday}",
            },
            "header_emojis",
            2,
        )
        step.execute()

    mock_generate.assert_called_once_with("Pick emojis for: Halloween")
    assert run_ctx.state["header_emojis"] == "\U0001f383\U0001f47b"


def test_artifact_written(run_ctx):
    run_ctx.state["holiday"] = "Christmas"

    step = SelectEmojisStep(
        run_ctx,
        {"provider": "placeholder", "inputs": ["holiday"], "template": "emoji for {holiday}"},
        "header_emojis",
        3,
    )
    step.execute()

    artifact = json.loads(run_ctx.run_dir.joinpath("3_header_emojis.json").read_text())
    assert artifact["output"] == "\U0001f389"
    assert artifact["prompt"] == "emoji for Christmas"
    assert artifact["inputs"] == {"holiday": "Christmas"}
