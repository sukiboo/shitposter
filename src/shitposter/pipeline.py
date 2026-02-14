from shitposter.artifacts import RunContext, write_summary
from shitposter.config import Settings
from shitposter.steps import STEPS


def execute(settings: Settings, ctx: RunContext):
    print(f"Run `{ctx.run_id}` has started...")

    if ctx.is_published and not ctx.force:
        print(f"Already published for `{ctx.run_id}`. Use `--force` to re-run.")
        return

    steps_metadata = {}
    for idx, (name, params) in enumerate(settings.run.steps.items()):
        step_cls = STEPS[params.type]
        step_config = params.model_dump(exclude={"type"})
        result = step_cls(ctx, step_config, name, idx).execute()
        steps_metadata[name] = result.metadata
        print(f"{name:>12} >> {result.summary}")

    write_summary(ctx, steps_metadata)
    print(f"Run summary saved to `{ctx.run_dir}`")
