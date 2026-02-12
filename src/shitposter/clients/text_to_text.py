from shitposter.clients.base import TextProvider


class PlaceholderTextProvider(TextProvider):
    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "Placeholder text"


class ConstantTextProvider(TextProvider):
    def __init__(self, **kwargs):
        self.text = kwargs.get("prompt", "")

    def generate(self, prompt: str) -> str:
        return self.text


class OpenAITextProvider(TextProvider):
    ALLOWED_MODELS = {"gpt-5-nano", "gpt-5-mini", "gpt-5", "gpt-5.1", "gpt-5.2"}

    def __init__(self, **kwargs):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = kwargs.get("model", "gpt-5-nano")
        temp = kwargs.get("temperature")
        self.temperature = temp if temp is not None else 1.0

        if self.model not in self.ALLOWED_MODELS:
            raise ValueError(
                f"Unsupported model '{self.model}'. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_MODELS))}"
            )

    def metadata(self) -> dict:
        return {"model": self.model, "temperature": self.temperature, **super().metadata()}

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""


TEXT_PROVIDERS: dict[str, type[TextProvider]] = {
    "placeholder": PlaceholderTextProvider,
    "constant": ConstantTextProvider,
    "openai": OpenAITextProvider,
}
