import json

from shitposter.artifacts import create_run_context
from shitposter.pipeline import execute


def test_dry_run_creates_artifacts(settings):
    ctx = create_run_context(settings.env, dry_run=True)
    execute(settings, ctx)

    assert ctx.run_dir.joinpath("setup.json").exists()
    assert ctx.run_dir.joinpath("image.png").exists()
    assert ctx.run_dir.joinpath("caption.json").exists()
    assert ctx.run_dir.joinpath("summary.json").exists()
    assert ctx.run_dir.joinpath("publish.json").exists()

    summary = json.loads(ctx.run_dir.joinpath("summary.json").read_text())
    assert summary["dry_run"] is True
    assert summary["published"] is False
    steps = summary["steps"]
    assert "setup" in steps
    assert "image" in steps
    assert "caption" in steps
    assert "publish" in steps


def test_idempotency_skips_published(settings):
    ctx = create_run_context(settings.env, dry_run=True)
    execute(settings, ctx)

    # First run creates summary.json, so second run should skip
    execute(settings, ctx)


def test_force_reruns(settings):
    ctx = create_run_context(settings.env, dry_run=True)
    execute(settings, ctx)

    _ = ctx.run_dir.joinpath("setup.json").read_text()

    ctx_force = create_run_context(settings.env, dry_run=True, force=True)
    execute(settings, ctx_force)

    assert ctx.run_dir.joinpath("setup.json").exists()
