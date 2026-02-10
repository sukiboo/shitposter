from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from shitposter.artifacts import RunContext


class StepResult(BaseModel):
    metadata: Any = {}
    summary: str = ""


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    provider: str


class Step(ABC):
    @abstractmethod
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult: ...
