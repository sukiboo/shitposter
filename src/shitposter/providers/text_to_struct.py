import random
from typing import Annotated

import regex
from pydantic import AfterValidator, BaseModel, Field

from shitposter.providers.base import (
    TextToCaptionProvider,
    TextToEmojiProvider,
    TextToIntProvider,
)


class PlaceholderTextToIntProvider(TextToIntProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str, entries: list[str]) -> int:
        return 0


class PlaceholderTextToEmojiProvider(TextToEmojiProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "\U0001f389"


class PlaceholderTextToCaptionProvider(TextToCaptionProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "Placeholder caption."


class OpenAITextToIntProvider(TextToIntProvider):
    name = "openai"
    ALLOWED_MODELS = {"gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"}
    ALLOWED_EFFORTS = {"none", "low", "medium", "high"}
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
        full_prompt = f"{prompt}\n\n{numbered}"
        text_format = self._response_model(len(entries))
        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.responses.parse(
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


class OpenAITextToEmojiProvider(TextToEmojiProvider):
    name = "openai"
    ALLOWED_MODELS = {"gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"}
    ALLOWED_EFFORTS = {"none", "low", "medium", "high"}
    MAX_RETRIES = 3
    MIN_COUNT = 1
    MAX_COUNT = 3
    _EMOJI_RE = regex.compile(r"^\p{Extended_Pictographic}+$")

    @staticmethod
    def _check_emoji(v: str) -> str:
        if not OpenAITextToEmojiProvider._EMOJI_RE.match(v):
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
                "emojis": Field(min_length=self.MIN_COUNT, max_length=self.MAX_COUNT),
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


class OpenAITextToCaptionProvider(TextToCaptionProvider):
    name = "openai"
    ALLOWED_MODELS = {"gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"}
    ALLOWED_EFFORTS = {"none", "low", "medium", "high"}
    MAX_RETRIES = 3

    _CaptionResponse = type(
        "CaptionResponse",
        (BaseModel,),
        {
            "__annotations__": {"caption": str},
            "caption": Field(
                min_length=50,
                max_length=350,
                description=(
                    "A concise, punchy social caption that makes the image feel "
                    "funnier; witty, internet-native, not a literal description."
                ),
            ),
        },
    )

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

    def generate(self, prompt: str) -> str:
        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.responses.parse(
                    model=self.model,
                    input=prompt,
                    text_format=self._CaptionResponse,
                    reasoning={"effort": self.effort},
                )
                parsed = response.output_parsed
                return parsed.caption  # type: ignore[union-attr]
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to unstructured")
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": self.effort},
        )
        return response.output_text
