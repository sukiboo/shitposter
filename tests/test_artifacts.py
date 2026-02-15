from shitposter.artifacts import create_run_context
from shitposter.config import EnvSettings


def test_create_run_context(tmp_path):
    env = EnvSettings(artifacts_path=tmp_path)
    ctx = create_run_context(env)
    assert ctx.run_id
    assert ctx.run_dir.exists()
    assert ctx.run_dir == tmp_path.joinpath(ctx.run_id)
