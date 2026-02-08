class TemplateCaptionProvider:
    def generate(self, template: str, topic: str, prompt: str) -> str:
        return template.format(topic=topic, prompt=prompt)
