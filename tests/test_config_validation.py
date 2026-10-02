from pathlib import Path

import pytest

from shitposter.config import RunConfig, load_run_config

CONFIGS = sorted(Path(__file__).parent.parent.joinpath("configs").glob("*.yaml"))


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
