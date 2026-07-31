from typing import Annotated

import regex
from pydantic import AfterValidator, BaseModel, Field

from shitposter.constants import (
    ANTHROPIC_TEXT_MODELS,
    OPENAI_EFFORT_LEVELS,
    OPENAI_TEXT_MODELS,
)
from shitposter.providers.anthropic_common import thinking_kwargs, validate_thinking
from shitposter.providers.base import TextToEmojiProvider

EMOJI_MIN_COUNT = 1
EMOJI_MAX_COUNT = 3
EMOJI_RE = regex.compile(r"^[\p{Extended_Pictographic}\p{Emoji_Component}\u200d\ufe0f\ufe0e]+$")


class PlaceholderTextToEmojiProvider(TextToEmojiProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "\U0001f389"


class OpenAITextToEmojiProvider(TextToEmojiProvider):
    """Generates 1-3 emoji via OpenAI structured output, validated with a Unicode regex."""

    name = "openai"
    ALLOWED_MODELS = OPENAI_TEXT_MODELS
    ALLOWED_EFFORTS = OPENAI_EFFORT_LEVELS
    MAX_RETRIES = 3

    @staticmethod
    def _check_emoji(v: str) -> str:
        if not EMOJI_RE.match(v):
            raise ValueError(f"Not an emoji: {v!r}")
        return v

    _Emoji = Annotated[str, AfterValidator(_check_emoji)]

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

    def _response_model(self) -> type[BaseModel]:
        emoji_type = self._Emoji
        return type(
            "EmojiList",
            (BaseModel,),
            {
                "__annotations__": {"emojis": list[emoji_type]},  # type: ignore[valid-type]
                "emojis": Field(min_length=EMOJI_MIN_COUNT, max_length=EMOJI_MAX_COUNT),
            },
        )

    def generate(self, prompt: str) -> str:
        text_format = self._response_model()
        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.responses.parse(
                    model=self.model,
                    input=prompt,
                    text_format=text_format,
                    reasoning={"effort": self.effort},
                )
                parsed = response.output_parsed
                return "".join(parsed.emojis)  # type: ignore[union-attr]
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to placeholder")
        return "\U0001f389"


class AnthropicTextToEmojiProvider(TextToEmojiProvider):
    """Generates 1-3 emoji via Anthropic tool use, validated with a Unicode regex."""

    name = "anthropic"
    ALLOWED_MODELS = ANTHROPIC_TEXT_MODELS
    MAX_RETRIES = 3

    _TOOL = {
        "name": "emojis",
        "description": "Return a list of emoji that match the prompt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "emojis": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": EMOJI_MIN_COUNT,
                    "maxItems": EMOJI_MAX_COUNT,
                    "description": "A list of 1-3 emoji characters.",
                }
            },
            "required": ["emojis"],
        },
    }

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

    def generate(self, prompt: str) -> str:
        for _ in range(self.MAX_RETRIES):
            try:
                kwargs: dict = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "tools": [self._TOOL],
                    "messages": [{"role": "user", "content": prompt}],
                }
                kwargs.update(thinking_kwargs(self.model, self.budget_tokens, self.effort))
                if "thinking" in kwargs:
                    kwargs["tool_choice"] = {"type": "auto"}
                else:
                    kwargs["tool_choice"] = {"type": "tool", "name": "emojis"}
                response = self.client.messages.create(**kwargs)
                block = next(b for b in response.content if b.type == "tool_use")
                emojis = block.input["emojis"]  # type: ignore[index]
                if not (EMOJI_MIN_COUNT <= len(emojis) <= EMOJI_MAX_COUNT):
                    self._meta["errors"].append(f"emoji count {len(emojis)} out of range")
                    continue
                result = "".join(emojis)
                if not EMOJI_RE.match(result):
                    self._meta["errors"].append(f"invalid emoji: {result!r}")
                    continue
                return result
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to placeholder")
        return "\U0001f389"
