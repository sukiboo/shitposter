import pytest

from shitposter.artifacts import RunContext
from shitposter.config import AppConfig, EnvSettings, Settings


@pytest.fixture
def run_ctx(tmp_path):
    run_dir = tmp_path.joinpath("2026-01-15_09-00-00")
    run_dir.mkdir(parents=True)
    return RunContext(run_id="2026-01-15_09-00-00", run_dir=run_dir)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        env=EnvSettings(
            telegram_channel_bot_token="fake-channel-token",
            telegram_channel_chat_id="fake-channel-chat",
            telegram_debug_bot_token="fake-debug-token",
            telegram_debug_chat_id="fake-debug-chat",
            artifacts_path=tmp_path,
        ),
        app=AppConfig(),
    )
