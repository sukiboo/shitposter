import json

from shitposter.artifacts import create_run_context
from shitposter.pipeline import execute


def test_dry_run_creates_artifacts(settings):
    ctx = create_run_context(settings.env, dry_run=True)
    execute(settings, ctx)

    assert ctx.run_dir.joinpath("0_setup.json").exists()
    assert ctx.run_dir.joinpath("1_image.json").exists()
    assert ctx.run_dir.joinpath("image.png").exists()
    assert ctx.run_dir.joinpath("2_caption.json").exists()
    assert ctx.run_dir.joinpath("3_publish.json").exists()
    assert ctx.run_dir.joinpath("summary.json").exists()

    summary = json.loads(ctx.run_dir.joinpath("summary.json").read_text())
    assert summary["dry_run"] is True
    assert summary["published"] is False
    steps = summary["steps"]
    assert "setup" in steps
    assert "image" in steps
    assert "caption" in steps
    assert "publish" in steps


def test_rerun_overwrites(settings):
    ctx = create_run_context(settings.env, dry_run=True)
    execute(settings, ctx)

    # Second run on same context overwrites artifacts
    execute(settings, ctx)

    assert ctx.run_dir.joinpath("summary.json").exists()
