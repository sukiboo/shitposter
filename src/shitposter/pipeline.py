from shitposter.artifacts import RunContext, write_summary
from shitposter.config import Settings
from shitposter.steps import STEPS


def execute(settings: Settings, ctx: RunContext):
    print(f"Run `{ctx.run_id}` has started...")

    steps_metadata = {}
    error = None
    try:
        for idx, (name, params) in enumerate(settings.run.steps.items()):
            step_cls = STEPS[params.type]
            step_config = params.model_dump(exclude={"type"})
            result = step_cls(ctx, step_config, name, idx).execute()
            steps_metadata[name] = result.metadata
            print(f"{name:>16} >> {result.summary}")
    except Exception as exc:
        error = str(exc)
        print(f"Pipeline failed: {error}")
        raise
    finally:
        write_summary(ctx, steps_metadata, error=error)
        print(f"Run summary saved to `{ctx.run_dir}`")
