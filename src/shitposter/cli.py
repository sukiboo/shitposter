from datetime import datetime
from typing import Annotated, Optional

import typer

app = typer.Typer()
run_app = typer.Typer()
app.add_typer(run_app, name="run", help="Execute the posting pipeline.")


@run_app.callback(invoke_without_command=True)
def run(
    at: Annotated[
        Optional[str],
        typer.Option("--at", help="Run timestamp (YYYY-MM-DD_HH-MM-SS). Defaults to now."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Generate artifacts but don't publish."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Force re-run even if already published."),
    ] = False,
):
    from shitposter.artifacts import RUN_ID_FORMAT
    from shitposter.config import load_settings
    from shitposter.pipeline import execute

    run_at = datetime.strptime(at, RUN_ID_FORMAT) if at else None
    settings = load_settings()
    execute(settings, run_at=run_at, dry_run=dry_run, force=force)
