from pathlib import Path

import pytest

from shitposter.config import RunConfig, load_run_config

CONFIGS = sorted(Path(__file__).parent.parent.joinpath("configs").glob("*.yaml"))
GROUNDING_RULE = (
    "Build the joke around an action, expression, or object clearly visible in the image. "
    "Add a second comedic beat whose connection is immediately understandable, "
    "without requiring an invented backstory."
)


def _make_config(steps: dict) -> RunConfig:
    return RunConfig.model_validate({"steps": steps})


def test_valid_template_with_matching_inputs():
    _make_config(
        {
            "setup": {"type": "generate_text", "provider": "placeholder"},
            "image": {
                "type": "generate_image",
                "provider": "placeholder",
                "inputs": ["setup"],
                "template": "Generate an image of {setup}",
            },
        }
    )


def test_template_placeholder_not_in_inputs():
    with pytest.raises(Exception, match="template references.*{'typo'}"):
        _make_config(
            {
                "setup": {"type": "generate_text", "provider": "placeholder"},
                "image": {
                    "type": "generate_image",
                    "provider": "placeholder",
                    "inputs": ["setup"],
                    "template": "Generate an image of {typo}",
                },
            }
        )


def test_context_placeholder_not_in_inputs():
    with pytest.raises(Exception, match="context references.*{'typo'}"):
        _make_config(
            {
                "holidays": {"type": "generate_text", "provider": "placeholder"},
                "holiday": {
                    "type": "choose_holiday",
                    "provider": "placeholder",
                    "inputs": ["holidays"],
                    "context": "Recent selections: {typo}",
                },
            }
        )


def test_inputs_without_template_passes():
    _make_config(
        {
            "setup": {"type": "generate_text", "provider": "placeholder"},
            "image": {
                "type": "generate_image",
                "provider": "placeholder",
                "inputs": ["setup"],
            },
        }
    )


def test_unused_input_in_template_passes():
    _make_config(
        {
            "setup": {"type": "generate_text", "provider": "placeholder"},
            "caption": {
                "type": "generate_text",
                "provider": "placeholder",
                "inputs": ["setup"],
                "template": "A caption",
            },
        }
    )


@pytest.mark.parametrize("path", CONFIGS, ids=lambda path: path.name)
def test_shipped_configs_are_valid(path):
    load_run_config(path)


@pytest.mark.parametrize("name", ["dev", "holiday"])
def test_active_caption_configs_use_image_and_grounding(name):
    config = load_run_config(Path(__file__).parent.parent / "configs" / f"{name}.yaml")
    caption = config.steps["caption_body"]

    assert caption.type == "generate_caption"
    assert set(caption.inputs) == {"holiday", "image", "header_emojis", "caption_history"}
    assert caption.model_extra is not None
    template = caption.model_extra["template"]
    assert "The attached image is the primary visual reference." in template
    assert GROUNDING_RULE in template
    assert "{prompt}" not in template
