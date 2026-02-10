from shitposter.artifacts import RunContext, write_summary
from shitposter.config import Settings
from shitposter.steps.construct_prompt import ConstructPromptStep
from shitposter.steps.generate_caption import GenerateCaptionStep
from shitposter.steps.generate_image import GenerateImageStep
from shitposter.steps.publish_post import PublishPostInput, PublishPostStep


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
    caption = GenerateCaptionStep().execute(ctx, settings.run.caption)
    print(f"Step 3: {ctx.caption=}")

    # step 4: publish post to the configured platforms
    publish = PublishPostStep().execute(ctx, PublishPostInput(platforms=settings.run.publish))
    if ctx.dry_run:
        print("Step 4: dry run -- skipping publish")
    elif not ctx.publish:
        print("Step 4: published to debug chat")
    else:
        providers = [r.provider for r in publish.results]
        print(f"Step 4: published to {', '.join(providers)}")

    # step 5: write a summary of the run
    write_summary(
        ctx,
        {
            "prompt": settings.run.prompt.prompt,
            "image": image.metadata,
            "caption": caption.metadata,
            "publish": [
                {"provider": r.provider, "message_id": r.message_id} for r in publish.results
            ],
        },
    )
    print(f"Step 5: run summary saved to `{ctx.run_dir}`")
