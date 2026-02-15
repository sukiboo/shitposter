import json

from shitposter.steps.publish_post import PublishPostStep


def test_dry_run_skips_publish(run_ctx):
    run_ctx.dry_run = True
    run_ctx.state["image"] = "/tmp/test.png"
    run_ctx.state["caption"] = "test caption"

    config = {"inputs": ["image", "caption"], "platforms": ["placeholder"]}
    step = PublishPostStep(run_ctx, config, "publish", 3)
    result = step.execute()

    assert result.summary == "dry run -- skipping publish"
    assert run_ctx.run_dir.joinpath("3_publish.json").exists()

    artifact = json.loads(run_ctx.run_dir.joinpath("3_publish.json").read_text())
    assert artifact[0]["provider"] == "placeholder"
    assert artifact[0]["message_id"] == ""


def test_placeholder_publish(run_ctx):
    run_ctx.state["image"] = "/tmp/test.png"
    run_ctx.state["caption"] = "test caption"

    config = {"inputs": ["image", "caption"], "platforms": ["placeholder"]}
    step = PublishPostStep(run_ctx, config, "publish", 3)
    result = step.execute()

    assert result.summary == "published to placeholder"
    assert run_ctx.run_dir.joinpath("3_publish.json").exists()

    artifact = json.loads(run_ctx.run_dir.joinpath("3_publish.json").read_text())
    assert artifact[0]["provider"] == "placeholder"
    assert artifact[0]["message_id"] == "0"
