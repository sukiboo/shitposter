import random

from pydantic import BaseModel, Field

from shitposter.constants import (
    ANTHROPIC_TEXT_MODELS,
    OPENAI_EFFORT_LEVELS,
    OPENAI_TEXT_MODELS,
)
from shitposter.providers.anthropic_common import thinking_kwargs, validate_thinking
from shitposter.providers.base import TextToIntProvider


class PlaceholderTextToIntProvider(TextToIntProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str, entries: list[str]) -> int:
        return 0


class OpenAITextToIntProvider(TextToIntProvider):
    """Picks one entry from a numbered list via OpenAI structured output (returns an int index)."""

    name = "openai"
    default_prompt = "Pick one of the following entries:"
    ALLOWED_MODELS = OPENAI_TEXT_MODELS
    ALLOWED_EFFORTS = OPENAI_EFFORT_LEVELS
    MAX_RETRIES = 3

    def __init__(self, **kwargs):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = kwargs.get("model", "gpt-5-nano")
        self.effort = kwargs.get("effort", "medium")

        if self.model not in self.ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported model '{self.model}'. " f"Allowed: {', '.join(self.ALLOWED_MODELS)}"
            )
        if self.effort not in self.ALLOWED_EFFORTS:
            raise ValueError(
                f"Unsupported effort '{self.effort}'. "
                f"Allowed: {', '.join(self.ALLOWED_EFFORTS)}"
            )

    def metadata(self) -> dict:
        return {**super().metadata(), "model": self.model, "effort": self.effort}

    @staticmethod
    def _response_model(n: int) -> type[BaseModel]:
        return type(
            "ChosenIndex",
            (BaseModel,),
            {"__annotations__": {"index": int}, "index": Field(ge=1, le=n)},
        )

    def generate(self, prompt: str, entries: list[str]) -> int:
        numbered = "\n".join(f"{i}. {entry}" for i, entry in enumerate(entries, 1))
        full_prompt = f"{prompt or self.default_prompt}\n\n{numbered}"
        text_format = self._response_model(len(entries))
        for _ in range(self.MAX_RETRIES):
            try:
                response = self._api_call(
                    self.client.responses.parse,
                    model=self.model,
                    input=full_prompt,
                    text_format=text_format,
                    reasoning={"effort": self.effort},
                )
                parsed = response.output_parsed
                return parsed.index - 1  # type: ignore[union-attr]
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to random")
        return random.randint(0, len(entries) - 1)


class AnthropicTextToIntProvider(TextToIntProvider):
    """Picks one entry from a numbered list via Anthropic tool use (returns an int index)."""

    name = "anthropic"
    default_prompt = "Pick one of the following entries:"
    ALLOWED_MODELS = ANTHROPIC_TEXT_MODELS
    MAX_RETRIES = 3

    def __init__(self, **kwargs):
        from anthropic import Anthropic

        self.client = Anthropic()
        self.model = kwargs.get("model", "claude-sonnet-4-6")
        self.max_tokens = int(kwargs.get("max_tokens", 1024))
        self.budget_tokens = int(kwargs["budget_tokens"]) if "budget_tokens" in kwargs else None
        self.effort = kwargs.get("effort")

        if self.model not in self.ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported model '{self.model}'. " f"Allowed: {', '.join(self.ALLOWED_MODELS)}"
            )
        validate_thinking(self.model, self.max_tokens, self.budget_tokens, self.effort)

    def metadata(self) -> dict:
        meta = {**super().metadata(), "model": self.model, "max_tokens": self.max_tokens}
        if self.budget_tokens is not None:
            meta["budget_tokens"] = self.budget_tokens
        if self.effort is not None:
            meta["effort"] = self.effort
        return meta

    @staticmethod
    def _tool(n: int) -> dict:
        return {
            "name": "choose",
            "description": "Choose one entry from the list by its number.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": n,
                        "description": "The 1-based index of the chosen entry.",
                    }
                },
                "required": ["index"],
            },
        }

    def generate(self, prompt: str, entries: list[str]) -> int:
        numbered = "\n".join(f"{i}. {entry}" for i, entry in enumerate(entries, 1))
        full_prompt = f"{prompt or self.default_prompt}\n\n{numbered}"
        tool = self._tool(len(entries))
        for _ in range(self.MAX_RETRIES):
            try:
                kwargs: dict = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "tools": [tool],
                    "messages": [{"role": "user", "content": full_prompt}],
                }
                kwargs.update(thinking_kwargs(self.model, self.budget_tokens, self.effort))
                if "thinking" in kwargs:
                    kwargs["tool_choice"] = {"type": "auto"}
                else:
                    kwargs["tool_choice"] = {"type": "tool", "name": "choose"}
                response = self._api_call(self.client.messages.create, **kwargs)
                block = next(b for b in response.content if b.type == "tool_use")
                index = int(block.input["index"])  # type: ignore[index]
                if 1 <= index <= len(entries):
                    return index - 1
                self._meta["errors"].append(f"index {index} out of range")
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to random")
        return random.randint(0, len(entries) - 1)
