import base64
from pathlib import Path

from pydantic import BaseModel, Field

from shitposter.constants import (
    ANTHROPIC_TEXT_MODELS,
    OPENAI_EFFORT_LEVELS,
    OPENAI_TEXT_MODELS,
)
from shitposter.providers.anthropic_common import thinking_kwargs, validate_thinking
from shitposter.providers.base import TextToCaptionProvider

CAPTION_IMAGE_MEDIA_TYPE = "image/png"
CAPTION_IMAGE_DETAIL = "auto"
CAPTION_MIN_LENGTH = 15
CAPTION_MAX_LENGTH = 180
CAPTION_DESCRIPTION = (
    "A short, punchy social caption that adds a second comedic beat to the image; "
    "specific, surprising, internet-native, and not a literal description."
)


class PlaceholderTextToCaptionProvider(TextToCaptionProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str, image_path: str | None = None) -> str:
        return "Placeholder caption."


class OpenAITextToCaptionProvider(TextToCaptionProvider):
    """Caption generation via OpenAI structured output, enforcing appropriate length."""

    name = "openai"
    ALLOWED_MODELS = OPENAI_TEXT_MODELS
    ALLOWED_EFFORTS = OPENAI_EFFORT_LEVELS
    MAX_RETRIES = 3

    _CaptionResponse = type(
        "CaptionResponse",
        (BaseModel,),
        {
            "__annotations__": {"caption": str},
            "caption": Field(
                min_length=CAPTION_MIN_LENGTH,
                max_length=CAPTION_MAX_LENGTH,
                description=CAPTION_DESCRIPTION,
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

    def generate(self, prompt: str, image_path: str | None = None) -> str:
        kwargs: dict = {
            "model": self.model,
            "input": prompt,
            "reasoning": {"effort": self.effort},
        }
        if image_path is not None:
            image_data = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
            kwargs["input"] = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:{CAPTION_IMAGE_MEDIA_TYPE};base64,{image_data}",
                            "detail": CAPTION_IMAGE_DETAIL,
                        },
                    ],
                }
            ]
        for _ in range(self.MAX_RETRIES):
            try:
                response = self._api_call(
                    self.client.responses.parse,
                    text_format=self._CaptionResponse,
                    **kwargs,
                )
                parsed = response.output_parsed
                return parsed.caption  # type: ignore[union-attr]
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to unstructured")
        response = self._api_call(self.client.responses.create, **kwargs)
        return response.output_text


class AnthropicTextToCaptionProvider(TextToCaptionProvider):
    """Caption generation via Anthropic tool use, enforcing appropriate length."""

    name = "anthropic"
    ALLOWED_MODELS = ANTHROPIC_TEXT_MODELS
    MAX_RETRIES = 3

    _TOOL = {
        "name": "caption",
        "description": "Return a social media caption for the image.",
        "input_schema": {
            "type": "object",
            "properties": {
                "caption": {
                    "type": "string",
                    "minLength": CAPTION_MIN_LENGTH,
                    "maxLength": CAPTION_MAX_LENGTH,
                    "description": CAPTION_DESCRIPTION,
                }
            },
            "required": ["caption"],
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

    def _api_kwargs(
        self, prompt: str, use_tool: bool = True, image_data: str | None = None
    ) -> dict:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if image_data is not None:
            kwargs["messages"][0]["content"] = [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": CAPTION_IMAGE_MEDIA_TYPE,
                        "data": image_data,
                    },
                },
            ]
        kwargs.update(thinking_kwargs(self.model, self.budget_tokens, self.effort))
        if use_tool:
            kwargs["tools"] = [self._TOOL]
            if "thinking" in kwargs:
                kwargs["tool_choice"] = {"type": "auto"}
            else:
                kwargs["tool_choice"] = {"type": "tool", "name": "caption"}
        return kwargs

    def generate(self, prompt: str, image_path: str | None = None) -> str:
        image_data = (
            base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
            if image_path is not None
            else None
        )
        for _ in range(self.MAX_RETRIES):
            try:
                response = self._api_call(
                    self.client.messages.create, **self._api_kwargs(prompt, image_data=image_data)
                )
                block = next(b for b in response.content if b.type == "tool_use")
                caption = str(block.input["caption"])  # type: ignore[index]
                if CAPTION_MIN_LENGTH <= len(caption) <= CAPTION_MAX_LENGTH:
                    return caption
                self._meta["errors"].append(f"caption length {len(caption)} out of range")
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to unstructured")
        response = self._api_call(
            self.client.messages.create,
            **self._api_kwargs(prompt, use_tool=False, image_data=image_data),
        )
        block = next(b for b in response.content if b.type == "text")
        return block.text
