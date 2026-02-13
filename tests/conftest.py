import pytest

from shitposter.artifacts import RunContext
from shitposter.config import EnvSettings, RunConfig, Settings


@pytest.fixture
def run_ctx(tmp_path):
    run_dir = tmp_path.joinpath("2026-01-15_09-00-00")
    run_dir.mkdir(parents=True)
    return RunContext(run_id="2026-01-15_09-00-00", run_dir=run_dir)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        env=EnvSettings(
            artifacts_path=tmp_path,
        ),
        run=RunConfig.model_validate(
            {
                "steps": {
                    "setup": {"type": "construct_prompt", "provider": "placeholder"},
                    "image": {
                        "type": "generate_image",
                        "provider": "placeholder",
                        "inputs": ["setup"],
                    },
                    "caption": {
                        "type": "generate_caption",
                        "provider": "placeholder",
                        "inputs": ["setup"],
                    },
                    "publish": {
                        "type": "publish_post",
                        "inputs": ["image", "caption"],
                        "platforms": ["placeholder"],
                    },
                }
            }
        ),
    )
