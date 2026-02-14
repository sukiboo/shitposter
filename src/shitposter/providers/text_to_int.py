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
    name = "openai"
    ALLOWED_MODELS = {"gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"}
    MAX_RETRIES = 3

    def __init__(self, **kwargs):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = kwargs.get("model", "gpt-5-nano")

        if self.model not in self.ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported model '{self.model}'. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_MODELS))}"
            )

    def metadata(self) -> dict:
        return {"model": self.model, **super().metadata()}

    @staticmethod
    def _response_model(n: int) -> type[BaseModel]:
        return type(
            "ChosenIndex",
            (BaseModel,),
            {"__annotations__": {"index": int}, "index": Field(ge=1, le=n)},
        )

    def generate(self, prompt: str, entries: list[str]) -> int:
        numbered = "\n".join(f"{i}: {entry}" for i, entry in enumerate(entries, 1))
        full_prompt = f"{prompt}\n\n{numbered}"
        response_format = self._response_model(len(entries))
        for _ in range(self.MAX_RETRIES):
            try:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[{"role": "user", "content": full_prompt}],
                    response_format=response_format,
                )
                parsed = response.choices[0].message.parsed
                return parsed.index - 1  # type: ignore[union-attr]
            except Exception as e:
                self._meta["errors"].append(str(e))
                continue
        self._meta["errors"].append("all retries failed, fell back to random")
        return random.randint(0, len(entries) - 1)
