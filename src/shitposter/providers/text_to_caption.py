from pydantic import BaseModel, Field

from shitposter.providers.base import TextToCaptionProvider


class PlaceholderTextToCaptionProvider(TextToCaptionProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "Placeholder caption."


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
