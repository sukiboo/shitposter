from shitposter.providers.base import TextProvider


class PlaceholderTextProvider(TextProvider):
    name = "placeholder"

    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "Placeholder text"


class ConstantTextProvider(TextProvider):
    name = "constant"

    def __init__(self, **kwargs):
        self.text = kwargs.get("prompt", "")

    def generate(self, prompt: str) -> str:
        return self.text or prompt


class OpenAITextProvider(TextProvider):
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
                f"Unsupported model '{self.model}'. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_MODELS))}"
            )
        if self.effort not in self.ALLOWED_EFFORTS:
            raise ValueError(
                f"Unsupported effort '{self.effort}'. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_EFFORTS))}"
            )

    def metadata(self) -> dict:
        return {"model": self.model, "effort": self.effort, **super().metadata()}

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": self.effort},
        )
        return response.output_text
