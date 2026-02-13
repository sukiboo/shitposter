from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel

from shitposter.artifacts import RunContext


class StepResult(BaseModel):
    metadata: Any = {}
    summary: str = "done"


class Step(ABC):
    registry: ClassVar[dict[str, type] | None] = None

    def __init__(self, ctx: RunContext, config: dict, name: str):
        self.ctx = ctx
        self.config = config
        self.name = name

        if self.registry is not None:
            provider_name = config["provider"]
            kwargs = {
                k: v for k, v in config.items() if k not in ("provider", "inputs", "template")
            }
            self.provider_name = provider_name
            self.provider = self.registry[provider_name](**kwargs)

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
        return {k: self.ctx.state[k] for k in self.config.get("inputs", [])}

    @property
    def output(self) -> Any:
        return self.ctx.state.get(self.name)

    @output.setter
    def output(self, value: Any) -> None:
        self.ctx.state[self.name] = value

    @abstractmethod
    def execute(self) -> StepResult: ...
