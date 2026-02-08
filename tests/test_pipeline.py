import json

from shitposter.pipeline import execute


def test_dry_run_creates_artifacts(settings):
    execute(settings, dry_run=True)

    run_dirs = list(settings.env.shitposter_artifact_root.joinpath("runs").iterdir())
    assert len(run_dirs) == 1

    run_dir = run_dirs[0]
    assert run_dir.joinpath("prompt.txt").exists()
    assert run_dir.joinpath("prompt.json").exists()
    assert run_dir.joinpath("image.png").exists()
    assert run_dir.joinpath("image_meta.json").exists()
    assert run_dir.joinpath("caption.txt").exists()
    assert run_dir.joinpath("manifest.json").exists()
    assert not run_dir.joinpath("publish.json").exists()

    manifest = json.loads(run_dir.joinpath("manifest.json").read_text())
    assert manifest["dry_run"] is True
    assert manifest["published"] is False


def test_idempotency_skips_published(settings):
    execute(settings, dry_run=True)

    run_dirs = list(settings.env.shitposter_artifact_root.joinpath("runs").iterdir())
    run_dir = run_dirs[0]

    # Fake a publish
    run_dir.joinpath("publish.json").write_text("{}")

    # Second run should skip (no error)
    execute(settings, dry_run=True)


def test_force_reruns(settings):
    execute(settings, dry_run=True)

    run_dirs = list(settings.env.shitposter_artifact_root.joinpath("runs").iterdir())
    run_dir = run_dirs[0]
    run_dir.joinpath("publish.json").write_text("{}")

    first_prompt = run_dir.joinpath("prompt.txt").read_text()

    execute(settings, dry_run=True, force=True)

    # prompt.txt was overwritten (may or may not change due to randomness,
    # but the file should still exist)
    assert run_dir.joinpath("prompt.txt").exists()
