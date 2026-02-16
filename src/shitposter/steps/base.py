import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel

from shitposter.artifacts import RunContext


class StepResult(BaseModel):
    metadata: Any = {}
    summary: str = "done"


class Step(ABC):
    registry: ClassVar[dict[str, type] | None]
    provider: Any = None

    def __init__(self, ctx: RunContext, config: dict, name: str, idx: int):
        self.ctx = ctx
        self.config = config
        self.name = name
        self.idx = idx

        if self.registry is not None:
            kwargs = {
                k: v for k, v in config.items() if k not in ("provider", "inputs", "template")
            }
            self.provider = self.registry[config["provider"]](**kwargs)

    @classmethod
    def validate_config(cls, config: dict) -> None:
        if cls.registry is not None:
            if "provider" not in config:
                raise ValueError(f"{cls.__name__} requires 'provider'")
            if config["provider"] not in cls.registry:
                raise ValueError(
                    f"Unknown provider '{config['provider']}'. " f"Allowed: {sorted(cls.registry)}"
                )

    @property
    def inputs(self) -> dict[str, Any]:
        if not hasattr(self, "_inputs"):
            self._inputs = {k: self.ctx.state[k] for k in self.config.get("inputs", [])}
        return self._inputs

    @property
    def output(self) -> Any:
        return self.ctx.state.get(self.name)

    @output.setter
    def output(self, value: Any) -> None:
        self.ctx.state[self.name] = value

    def artifact_path(self, ext: str = "json") -> Path:
        return self.ctx.run_dir / f"{self.idx}_{self.name}.{ext}"

    def write_artifact(self, data: Any) -> None:
        self.artifact_path().write_text(json.dumps(data, indent=2, default=str))

    @property
    def metadata(self) -> dict:
        return {
            "params": self.provider.metadata() if self.provider else {},
            "inputs": self.inputs,
            "output": self.output,
        }

    @property
    def template(self) -> str:
        return self.config.get("template", "")

    @abstractmethod
    def execute(self) -> StepResult: ...
