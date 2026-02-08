from shitposter.artifacts import RunContext, write_summary
from shitposter.config import Settings
from shitposter.steps.construct_prompt import ConstructPromptInput, ConstructPromptStep
from shitposter.steps.generate_caption import GenerateCaptionInput, GenerateCaptionStep
from shitposter.steps.generate_image import GenerateImageInput, GenerateImageStep
from shitposter.steps.publish_post import PublishPostInput, PublishPostStep


def execute(settings: Settings, ctx: RunContext):
    print(f"Run {ctx.run_id}...")

    if ctx.is_published and not ctx.force:
        print(f"Already published for {ctx.run_id}. Use `--force` to re-run.")
        return

    # step 1: construct the image generation prompt
    #  input: prompt text
    # output: image generation prompt
    image_prompt = ConstructPromptStep().execute(
        ctx,
        ConstructPromptInput(
            prompt=settings.run.prompt.prompt,
        ),
    )
    print(f"Step 1: {image_prompt.prompt=}")

    # step 2: generate an image from the prompt
    #  input: image prompt, image provider
    # output: image file path, provider metadata
    image = GenerateImageStep().execute(
        ctx,
        GenerateImageInput(
            prompt=image_prompt.prompt,
            provider=settings.run.image.provider,
        ),
    )
    print(f"Step 2: {image.image_path=}")

    # step 3: generate the post caption
    #  input: image prompt, caption provider
    # output: caption text
    caption = GenerateCaptionStep().execute(
        ctx,
        GenerateCaptionInput(
            prompt=image_prompt.prompt,
            provider=settings.run.caption.provider,
        ),
    )
    print(f"Step 3: {caption.caption_text=}")

    # step 4: publish post to the configured platforms
    #  input: image path, caption text
    # output: publish.json with message ID + response
    PublishPostStep(
        env=settings.env,
        platform=settings.run.publish.platform,
        publish=ctx.publish,
    ).execute(
        ctx,
        PublishPostInput(
            image_path=image.image_path,
            caption=caption.caption_text,
        ),
    )
    if ctx.dry_run:
        print("Step 4: dry run -- skipping publish")
    else:
        target = settings.run.publish.platform if ctx.publish else "debug chat"
        print(f"Step 4: published to {target}")

    # step 5: write a summary of the run
    write_summary(ctx, settings.run.model_dump())
    print(f"Step 5: run summary saved to `{ctx.run_dir}`")
