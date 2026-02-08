import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class RunContext(BaseModel):
    run_id: str
    run_dir: Path

    @property
    def prompt_txt(self) -> Path:
        return self.run_dir.joinpath("prompt.txt")

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
    def caption_txt(self) -> Path:
        return self.run_dir.joinpath("caption.txt")

    @property
    def publish_json(self) -> Path:
        return self.run_dir.joinpath("publish.json")

    @property
    def manifest_json(self) -> Path:
        return self.run_dir.joinpath("manifest.json")

    @property
    def is_published(self) -> bool:
        return self.publish_json.exists()


RUN_ID_FORMAT = "%Y-%m-%d_%H-%M-%S"


def create_run_context(artifact_root: Path, run_at: datetime | None = None) -> RunContext:
    run_id = (run_at or datetime.now()).strftime(RUN_ID_FORMAT)
    run_dir = artifact_root.joinpath(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunContext(run_id=run_id, run_dir=run_dir)


def write_manifest(ctx: RunContext, config: dict, dry_run: bool):
    manifest = {
        "run_id": ctx.run_id,
        "dry_run": dry_run,
        "config": config,
        "published": ctx.is_published,
    }
    ctx.manifest_json.write_text(json.dumps(manifest, indent=2))
