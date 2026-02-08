from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

RUN_ID_FORMAT = "%Y-%m-%d_%H-%M-%S"


def create_run_context(
    artifact_root: Path,
    run_at: datetime | None = None,
    dry_run: bool = False,
    force: bool = False,
    publish: bool = False,
) -> RunContext:
    run_id = (run_at or datetime.now()).strftime(RUN_ID_FORMAT)
    run_dir = artifact_root.joinpath(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunContext(
        run_id=run_id,
        run_dir=run_dir,
        dry_run=dry_run,
        force=force,
        publish=publish,
    )


def write_summary(ctx: RunContext, config: dict):
    summary = {
        "run_id": ctx.run_id,
        "timestamp": datetime.now().isoformat(),
        "dry_run": ctx.dry_run,
        "published": ctx.publish and not ctx.dry_run,
        "config": config,
    }
    ctx.summary_json.write_text(json.dumps(summary, indent=2))


class RunContext(BaseModel):
    run_id: str
    run_dir: Path
    dry_run: bool = False
    force: bool = False
    publish: bool = False

    @property
    def prompt_json(self) -> Path:
        return self.run_dir.joinpath("prompt.json")

    @property
    def image_path(self) -> Path:
        return self.run_dir.joinpath("image.png")

    @property
    def image_meta_json(self) -> Path:
        return self.run_dir.joinpath("image_meta.json")

    @property
    def caption_json(self) -> Path:
        return self.run_dir.joinpath("caption.json")

    @property
    def publish_json(self) -> Path:
        return self.run_dir.joinpath("publish.json")

    @property
    def summary_json(self) -> Path:
        return self.run_dir.joinpath("summary.json")

    @property
    def is_published(self) -> bool:
        return self.publish_json.exists()
