from shitposter.artifacts import RunContext
from shitposter.clients.text_to_image import IMAGE_PROVIDERS
from shitposter.steps.base import ProviderConfig, Step, StepResult


class GenerateImageStep(Step):
    def execute(self, ctx: RunContext, config: dict, key: str) -> StepResult:
        cfg = ProviderConfig.model_validate(config)
        provider_cls = IMAGE_PROVIDERS[cfg.provider]
        provider = provider_cls(**cfg.model_dump(exclude={"provider"}))
        image_data = provider.generate(ctx.state["prompt"])

        image_path = ctx.run_dir.joinpath(f"{key}.png")
        image_path.write_bytes(image_data)
        ctx.state["image_path"] = str(image_path)

        metadata = {"provider": cfg.provider, "prompt": ctx.state["prompt"], **provider.metadata()}
        return StepResult(metadata=metadata, summary=f"image_path={image_path}")
