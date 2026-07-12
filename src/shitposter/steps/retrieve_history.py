import json

from shitposter.steps.base import Step, StepResult

DEFAULT_RUNS = 7
EMPTY_HISTORY = "(no recent posts)"


class RetrieveHistoryStep(Step):
    registry = None

    @classmethod
    def validate_config(cls, config: dict) -> None:
        if not config.get("step"):
            raise ValueError("retrieve_history requires 'step'")

    def execute(self) -> StepResult:
        step = self.config["step"]
        runs = self.config.get("runs", DEFAULT_RUNS)

        entries: list[str] = []
        for run_dir in sorted(self.ctx.run_dir.parent.iterdir(), reverse=True):
            if run_dir.name == self.ctx.run_id or not run_dir.is_dir():
                continue
            try:
                summary = json.loads(run_dir.joinpath("summary.json").read_text())
                if not summary["published"]:
                    continue
                output = summary["steps"][step]["output"]
            except (OSError, json.JSONDecodeError, KeyError):
                # incomplete, failed, or older-format runs carry no usable history
                continue
            entries.append(f"- {run_dir.name[:10]}: {output}")
            if len(entries) >= runs:
                break

        self.output = "\n".join(entries) if entries else EMPTY_HISTORY

        artifact = {**self.metadata, "step": step}
        self.write_artifact(artifact)

        return StepResult(
            metadata=self.metadata, summary=f"collected {len(entries)} past {step!r} outputs"
        )
