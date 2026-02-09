class PlaceholderCaptionProvider:
    def __init__(self, **kwargs):
        pass

    def generate(self, prompt: str) -> str:
        return "Placeholder caption"


class OpenAICaptionProvider:
    def __init__(self, **kwargs):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = kwargs.get("model") or "gpt-4o-mini"

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""
