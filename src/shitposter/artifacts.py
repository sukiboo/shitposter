from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from shitposter.config import EnvSettings

RUN_ID_FORMAT = "%Y-%m-%d_%H-%M-%S"


def create_run_context(
    env: EnvSettings,
    run_at: datetime | None = None,
    dry_run: bool = False,
    force: bool = False,
    publish: bool = False,
) -> RunContext:
    run_id = (run_at or datetime.now()).strftime(RUN_ID_FORMAT)
    run_dir = env.artifacts_path.joinpath(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunContext(
        env=env,
        run_id=run_id,
        run_dir=run_dir,
        dry_run=dry_run,
        force=force,
        publish=publish,
    )


def write_summary(ctx: RunContext, steps: dict) -> None:
    summary = {
        "run_id": ctx.run_id,
        "timestamp": datetime.now().isoformat(),
        "dry_run": ctx.dry_run,
        "published": ctx.publish and not ctx.dry_run,
        "steps": steps,
    }
    ctx.run_dir.joinpath("summary.json").write_text(json.dumps(summary, indent=2))


class RunContext(BaseModel):
    env: EnvSettings | None = None
    run_id: str
    run_dir: Path
    dry_run: bool = False
    force: bool = False
    publish: bool = False
    state: dict = {}

    @property
    def is_published(self) -> bool:
        return self.run_dir.joinpath("summary.json").exists()
