import json

import pytest

from shitposter.steps.retrieve_history import EMPTY_HISTORY, RetrieveHistoryStep


def _make_run(root, run_id, published=True, steps=None, with_summary=True):
    run_dir = root.joinpath(run_id)
    run_dir.mkdir()
    if with_summary:
        summary = {"run_id": run_id, "published": published, "steps": steps or {}}
        run_dir.joinpath("summary.json").write_text(json.dumps(summary))


def test_collects_newest_first(run_ctx, tmp_path):
    for day in (10, 11, 12):
        _make_run(tmp_path, f"2026-01-{day}_09-00-00", steps={"prompt": {"output": f"p{day}"}})

    step = RetrieveHistoryStep(run_ctx, {"step": "prompt"}, "prompt_history", 0)
    result = step.execute()

    assert run_ctx.state["prompt_history"] == (
        "- 2026-01-12: p12\n- 2026-01-11: p11\n- 2026-01-10: p10"
    )
    assert result.summary == "collected 3 past 'prompt' outputs"
    assert run_ctx.run_dir.joinpath("0_prompt_history.json").exists()


def test_respects_runs_limit(run_ctx, tmp_path):
    for day in range(1, 6):
        _make_run(tmp_path, f"2026-01-{day:02d}_09-00-00", steps={"prompt": {"output": f"p{day}"}})

    step = RetrieveHistoryStep(run_ctx, {"step": "prompt", "runs": 2}, "prompt_history", 0)
    step.execute()

    assert run_ctx.state["prompt_history"] == "- 2026-01-05: p5\n- 2026-01-04: p4"


def test_skips_unusable_runs(run_ctx, tmp_path):
    _make_run(tmp_path, "2026-01-10_09-00-00", steps={"prompt": {"output": "keep"}})
    _make_run(tmp_path, "2026-01-11_09-00-00", published=False, steps={"prompt": {"output": "dry"}})
    _make_run(tmp_path, "2026-01-12_09-00-00", with_summary=False)
    _make_run(tmp_path, "2026-01-13_09-00-00", steps={"other": {"output": "no prompt step"}})
    run_ctx.run_dir.joinpath("summary.json").write_text(
        json.dumps({"published": True, "steps": {"prompt": {"output": "current run"}}})
    )

    step = RetrieveHistoryStep(run_ctx, {"step": "prompt"}, "prompt_history", 0)
    step.execute()

    assert run_ctx.state["prompt_history"] == "- 2026-01-10: keep"


def test_empty_history(run_ctx):
    step = RetrieveHistoryStep(run_ctx, {"step": "prompt"}, "prompt_history", 0)
    result = step.execute()

    assert run_ctx.state["prompt_history"] == EMPTY_HISTORY
    assert result.summary == "collected 0 past 'prompt' outputs"


def test_requires_step_key():
    with pytest.raises(ValueError, match="requires 'step'"):
        RetrieveHistoryStep.validate_config({"runs": 7})
