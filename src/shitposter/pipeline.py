from datetime import datetime

from shitposter.artifacts import create_run_context, write_manifest
from shitposter.clients.telegram import TelegramClient
from shitposter.config import Settings
from shitposter.steps.caption import CaptionInput, CaptionStep
from shitposter.steps.image import ImageInput, ImageStep
from shitposter.steps.prompt import PromptInput, PromptStep
from shitposter.steps.publish import PublishInput, PublishStep


def execute(
    settings: Settings,
    run_at: datetime | None = None,
    dry_run: bool = False,
    force: bool = False,
):
    ctx = create_run_context(settings.env.shitposter_artifact_root, run_at)
    print(f"Run {ctx.run_id} → {ctx.run_dir}")

    if ctx.is_published and not force:
        print(f"Already published for {ctx.run_id}. Use --force to re-run.")
        return

    # step 1: pick a random topic and expand it into an image-generation prompt
    #  input: template string, topic list
    # output: prompt text, chosen topic
    prompt_out = PromptStep().execute(
        ctx,
        PromptInput(
            template=settings.app.prompt.template,
            topics=settings.app.prompt.topics,
        ),
    )
    print(f"Prompt: {prompt_out.prompt}")

    # step 2: generate an image from the prompt (provider-dependent)
    #  input: prompt text, provider name, dimensions
    # output: image file path, provider metadata
    image_out = ImageStep().execute(
        ctx,
        ImageInput(
            prompt=prompt_out.prompt,
            provider=settings.app.image.provider,
            width=settings.app.image.width,
            height=settings.app.image.height,
        ),
    )
    print(f"Image: {image_out.image_path}")

    # step 3: build the post caption from the prompt, topic, and image metadata
    #  input: prompt text, topic, template, image metadata
    # output: caption text
    caption_out = CaptionStep().execute(
        ctx,
        CaptionInput(
            prompt=prompt_out.prompt,
            topic=prompt_out.topic,
            template=settings.app.caption.template,
            image_metadata=image_out.metadata,
        ),
    )
    print(f"Caption: {caption_out.caption}")

    # step 4: send the image + caption to the configured platform
    #  input: image path, caption
    # output: publish.json with message ID + response
    if dry_run:
        print("Dry run — skipping publish.")
    else:
        publisher = TelegramClient(
            bot_token=settings.env.telegram_bot_token,
            chat_id=settings.env.telegram_chat_id,
        )
        PublishStep(publisher=publisher, platform=settings.app.publish.platform).execute(
            ctx,
            PublishInput(
                image_path=image_out.image_path,
                caption=caption_out.caption,
            ),
        )
        print(f"Published to {settings.app.publish.platform}.")

    # step 5: write a summary of the run (config, run_id, dry_run flag, publish status)
    write_manifest(ctx, settings.app.model_dump(), dry_run)
