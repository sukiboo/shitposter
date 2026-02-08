from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from shitposter.artifacts import RunContext

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class Step(ABC, Generic[TInput, TOutput]):
    @abstractmethod
    def execute(self, ctx: RunContext, input: TInput) -> TOutput: ...
