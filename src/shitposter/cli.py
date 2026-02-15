from pathlib import Path
from typing import Annotated, Optional

import typer

app = typer.Typer()
run_app = typer.Typer()
app.add_typer(run_app, name="run", help="Execute the posting pipeline.")


@run_app.callback(invoke_without_command=True)
def run(
    steps: Annotated[
        Optional[str],
        typer.Option("-s", "--steps", help="Config name in `configs/`. Defaults to dev.yaml"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Generate artifacts but don't publish."),
    ] = False,
):
    from shitposter.artifacts import create_run_context
    from shitposter.config import load_settings
    from shitposter.pipeline import execute

    steps_path = Path(f"configs/{steps}.yaml") if steps else Path("configs/dev.yaml")
    settings = load_settings(steps_path)
    ctx = create_run_context(settings.env, dry_run=dry_run)
    execute(settings, ctx)
