from datetime import datetime

from shitposter.artifacts import create_run_context
from shitposter.config import EnvSettings


def test_is_published_false_by_default(run_ctx):
    assert not run_ctx.is_published


def test_is_published_true_when_file_exists(run_ctx):
    run_ctx.run_dir.joinpath("summary.json").write_text("{}")
    assert run_ctx.is_published


def test_create_run_context(tmp_path):
    env = EnvSettings(artifacts_path=tmp_path)
    ctx = create_run_context(env, datetime(2026, 3, 15, 14, 30, 0))
    assert ctx.run_id == "2026-03-15_14-30-00"
    assert ctx.run_dir.exists()
    assert ctx.run_dir == tmp_path.joinpath("2026-03-15_14-30-00")
