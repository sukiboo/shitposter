from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from shitposter.artifacts import RunContext


class StepResult(BaseModel):
    metadata: Any = {}
    summary: str = ""


class Step(ABC):
    @abstractmethod
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult: ...


def setup_provider(registry: dict, config: dict) -> tuple[str, Any]:
    provider_name = config["provider"]
    provider_kwargs = {k: v for k, v in config.items() if k not in ("provider", "template")}
    return provider_name, registry[provider_name](**provider_kwargs)
