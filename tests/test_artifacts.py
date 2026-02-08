from datetime import datetime

from shitposter.artifacts import create_run_context


def test_run_context_paths(run_ctx):
    assert run_ctx.prompt_txt.name == "prompt.txt"
    assert run_ctx.image_path.name == "image.png"
    assert run_ctx.caption_txt.name == "caption.txt"
    assert run_ctx.publish_json.name == "publish.json"
    assert run_ctx.manifest_json.name == "manifest.json"


def test_is_published_false_by_default(run_ctx):
    assert not run_ctx.is_published


def test_is_published_true_when_file_exists(run_ctx):
    run_ctx.publish_json.write_text("{}")
    assert run_ctx.is_published


def test_create_run_context(tmp_path):
    ctx = create_run_context(tmp_path, datetime(2026, 3, 15, 14, 30, 0))
    assert ctx.run_id == "2026-03-15_14-30-00"
    assert ctx.run_dir.exists()
    assert ctx.run_dir == tmp_path.joinpath("runs", "2026-03-15_14-30-00")
