from shitposter.artifacts import RunContext, write_summary
from shitposter.config import Settings
from shitposter.steps import STEPS


def execute(settings: Settings, ctx: RunContext):
    print(f"Run `{ctx.run_id}` has started...")

    if ctx.is_published and not ctx.force:
        print(f"Already published for `{ctx.run_id}`. Use `--force` to re-run.")
        return

    steps_metadata = {}
    for key, entry in settings.run.steps.items():
        step_cls = STEPS[entry.type]
        step_config = entry.model_dump(exclude={"type"})
        result = step_cls().execute(ctx, step_config, key)
        steps_metadata[key] = result.metadata
        print(f"{key:>12} >> {result.summary or 'done'}")

    write_summary(ctx, steps_metadata)
    print(f"Run summary saved to `{ctx.run_dir}`")
