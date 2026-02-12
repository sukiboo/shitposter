from shitposter.artifacts import RunContext
from shitposter.clients.text_to_image import IMAGE_PROVIDERS
from shitposter.steps.base import Step, StepResult, setup_provider


class GenerateImageStep(Step):
    @classmethod
    def validate_config(cls, config: dict) -> None:
        if "provider" not in config:
            raise ValueError("generate_image requires 'provider'")
        if config["provider"] not in IMAGE_PROVIDERS:
            raise ValueError(
                f"Unknown image provider '{config['provider']}'. "
                f"Allowed: {sorted(IMAGE_PROVIDERS)}"
            )

    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        provider_name, provider = setup_provider(IMAGE_PROVIDERS, config)

        template = config.get("template")
        prompt = template.format(**ctx.state) if template else ctx.state["prompt"]
        image_data = provider.generate(prompt)

        metadata = {"provider": provider_name, **provider.metadata(), "prompt": prompt}
        image_path = ctx.run_dir.joinpath(f"{key}.png")
        image_path.write_bytes(image_data)
        ctx.state["image_path"] = str(image_path)

        return StepResult(metadata=metadata, summary=f"{image_path}")
