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
    ALLOWED_MODELS = {"gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"}
    ALLOWED_EFFORTS = {"none", "low", "medium", "high"}

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
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": self.effort},
        )
        return response.output_text


class AnthropicTextProvider(TextProvider):

    name = "anthropic"
    ALLOWED_MODELS = {"claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"}

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

    def generate(self, prompt: str) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.budget_tokens is not None:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.budget_tokens}
        response = self.client.messages.create(**kwargs)
        block = next(b for b in response.content if b.type == "text")
        return block.text
