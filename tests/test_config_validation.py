import pytest

from shitposter.config import RunConfig


def _make_config(steps: dict) -> RunConfig:
    return RunConfig.model_validate({"steps": steps})


def test_valid_template_with_matching_inputs():
    _make_config(
        {
            "setup": {"type": "construct_prompt", "provider": "placeholder"},
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
                "setup": {"type": "construct_prompt", "provider": "placeholder"},
                "image": {
                    "type": "generate_image",
                    "provider": "placeholder",
                    "inputs": ["setup"],
                    "template": "Generate an image of {typo}",
                },
            }
        )


def test_inputs_without_template_passes():
    _make_config(
        {
            "setup": {"type": "construct_prompt", "provider": "placeholder"},
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
            "setup": {"type": "construct_prompt", "provider": "placeholder"},
            "caption": {
                "type": "generate_caption",
                "provider": "placeholder",
                "inputs": ["setup"],
                "template": "A caption",
            },
        }
    )
