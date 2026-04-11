from pydantic import BaseModel, Field

from shitposter.providers.base import TextToCaptionProvider

CAPTION_MIN_LENGTH = 50
CAPTION_MAX_LENGTH = 350
CAPTION_DESCRIPTION = (
    "A concise, punchy social caption that makes the image feel "
    "funnier; witty, internet-native, not a literal description."
)


class PlaceholderTextToCaptionProvider(TextToCaptionProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "Placeholder caption."


class OpenAITextToCaptionProvider(TextToCaptionProvider):
    """Caption generation via OpenAI structured output, enforcing appropriate length."""

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


class AnthropicTextToCaptionProvider(TextToCaptionProvider):
    """Caption generation via Anthropic tool use, enforcing appropriate length."""

    name = "anthropic"
    ALLOWED_MODELS = {"claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"}
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

        if self.model not in self.ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported model '{self.model}'. " f"Allowed: {', '.join(self.ALLOWED_MODELS)}"
            )
        if self.budget_tokens is not None:
            if self.budget_tokens < 1024:
                raise ValueError("budget_tokens must be at least 1024")
            if self.budget_tokens >= self.max_tokens:
                raise ValueError("max_tokens must be greater than budget_tokens")

    def metadata(self) -> dict:
        meta = {**super().metadata(), "model": self.model, "max_tokens": self.max_tokens}
        if self.budget_tokens is not None:
            meta["budget_tokens"] = self.budget_tokens
        return meta

    def _api_kwargs(self, prompt: str, use_tool: bool = True) -> dict:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if use_tool:
            kwargs["tools"] = [self._TOOL]
            if self.budget_tokens is not None:
                kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.budget_tokens}
                kwargs["tool_choice"] = {"type": "auto"}
            else:
                kwargs["tool_choice"] = {"type": "tool", "name": "caption"}
        elif self.budget_tokens is not None:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.budget_tokens}
        return kwargs

    def generate(self, prompt: str) -> str:
        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.messages.create(**self._api_kwargs(prompt))
                block = next(b for b in response.content if b.type == "tool_use")
                caption = str(block.input["caption"])  # type: ignore[index]
                if CAPTION_MIN_LENGTH <= len(caption) <= CAPTION_MAX_LENGTH:
                    return caption
                self._meta["errors"].append(f"caption length {len(caption)} out of range")
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to unstructured")
        response = self.client.messages.create(**self._api_kwargs(prompt, use_tool=False))
        block = next(b for b in response.content if b.type == "text")
        return block.text
