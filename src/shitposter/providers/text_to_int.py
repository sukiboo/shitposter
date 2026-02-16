import random

from pydantic import BaseModel, Field

from shitposter.providers.base import TextToIntProvider


class PlaceholderTextToIntProvider(TextToIntProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str, entries: list[str]) -> int:
        return 0


class OpenAITextToIntProvider(TextToIntProvider):
    """Picks one entry from a numbered list via structured output (returns an int index)."""

    name = "openai"
    default_prompt = "Pick one of the following entries:"
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
        full_prompt = f"{prompt or self.default_prompt}\n\n{numbered}"
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
