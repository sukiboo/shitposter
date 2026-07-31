from shitposter.constants import (
    ANTHROPIC_TEXT_MODELS,
    OPENAI_EFFORT_LEVELS,
    OPENAI_TEXT_MODELS,
)
from shitposter.providers.anthropic_common import thinking_kwargs, validate_thinking
from shitposter.providers.base import TextProvider


class PlaceholderTextProvider(TextProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "Placeholder text"


class ConstantTextProvider(TextProvider):
    """Returns a fixed string from the `prompt` config key, ignoring the template."""

    name = "constant"

    def __init__(self, **kwargs):
        self.text = kwargs.get("prompt", "")

    def generate(self, prompt: str) -> str:
        return self.text or prompt


class OpenAITextProvider(TextProvider):
    """Free-form text generation via OpenAI responses API."""

    name = "openai"
    ALLOWED_MODELS = OPENAI_TEXT_MODELS
    ALLOWED_EFFORTS = OPENAI_EFFORT_LEVELS

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
        response = self._api_call(
            self.client.responses.create,
            model=self.model,
            input=prompt,
            reasoning={"effort": self.effort},
        )
        return response.output_text


class AnthropicTextProvider(TextProvider):

    name = "anthropic"
    ALLOWED_MODELS = ANTHROPIC_TEXT_MODELS

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
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        kwargs.update(thinking_kwargs(self.model, self.budget_tokens, self.effort))
        response = self._api_call(self.client.messages.create, **kwargs)
        block = next(b for b in response.content if b.type == "text")
        return block.text
