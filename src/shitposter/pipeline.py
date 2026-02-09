from shitposter.artifacts import RunContext, write_summary
from shitposter.config import Settings
from shitposter.steps.construct_prompt import ConstructPromptStep
from shitposter.steps.generate_caption import GenerateCaptionStep
from shitposter.steps.generate_image import GenerateImageStep
from shitposter.steps.publish_post import PublishPostStep


def execute(settings: Settings, ctx: RunContext):
    print(f"Run {ctx.run_id}...")

    if ctx.is_published and not ctx.force:
        print(f"Already published for {ctx.run_id}. Use `--force` to re-run.")
        return

    # step 1: construct the image generation prompt
    ConstructPromptStep().execute(ctx, settings.run.prompt)
    print(f"Step 1: {ctx.prompt=}")

    # step 2: generate an image from the prompt
    image = GenerateImageStep().execute(ctx, settings.run.image)
    print(f"Step 2: {image.image_path=}")

    # step 3: generate the post caption
    GenerateCaptionStep().execute(ctx, settings.run.caption)
    print(f"Step 3: {ctx.caption=}")

    # step 4: publish post to the configured platforms
    PublishPostStep().execute(ctx, settings.run.publish)
    if ctx.dry_run:
        print("Step 4: dry run -- skipping publish")
    else:
        target = settings.run.publish.platform if ctx.publish else "debug chat"
        print(f"Step 4: published to {target}")

    # step 5: write a summary of the run
    write_summary(ctx, settings.run.model_dump())
    print(f"Step 5: run summary saved to `{ctx.run_dir}`")
