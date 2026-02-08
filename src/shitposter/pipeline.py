from datetime import datetime

from shitposter.artifacts import create_run_context, write_summary
from shitposter.clients.telegram import TelegramClient
from shitposter.config import Settings
from shitposter.steps.construct_prompt import ConstructPromptInput, ConstructPromptStep
from shitposter.steps.generate_caption import GenerateCaptionInput, GenerateCaptionStep
from shitposter.steps.generate_image import GenerateImageInput, GenerateImageStep
from shitposter.steps.publish_post import PublishPostInput, PublishPostStep


def execute(
    settings: Settings,
    run_at: datetime | None = None,
    dry_run: bool = False,
    force: bool = False,
    publish: bool = False,
):
    ctx = create_run_context(settings.env.artifacts_path, run_at)
    print(f"Run {ctx.run_id} → {ctx.run_dir}")

    if ctx.is_published and not force:
        print(f"Already published for {ctx.run_id}. Use --force to re-run.")
        return

    # step 1: construct the image-generation prompt
    #  input: prompt string
    # output: prompt text
    prompt_out = ConstructPromptStep().execute(
        ctx,
        ConstructPromptInput(
            prompt=settings.run.prompt.prompt,
        ),
    )
    print(f"Prompt: {prompt_out.prompt}")

    # step 2: generate an image from the prompt (provider-dependent)
    #  input: prompt text, provider name, dimensions
    # output: image file path, provider metadata
    image_out = GenerateImageStep().execute(
        ctx,
        GenerateImageInput(
            prompt=prompt_out.prompt,
            provider=settings.run.image.provider,
        ),
    )
    print(f"Image: {image_out.image_path}")

    # step 3: generate the post caption
    #  input: prompt text, provider name
    # output: caption text
    caption_out = GenerateCaptionStep().execute(
        ctx,
        GenerateCaptionInput(
            prompt=prompt_out.prompt,
            provider=settings.run.caption.provider,
        ),
    )
    print(f"Caption: {caption_out.caption}")

    # step 4: send the image + caption to the configured platform
    #  input: image path, caption
    # output: publish.json with message ID + response
    if dry_run:
        print("Dry run — skipping publish.")
    else:
        if publish:
            bot_token = settings.env.telegram_channel_bot_token
            chat_id = settings.env.telegram_channel_chat_id
        else:
            bot_token = settings.env.telegram_debug_bot_token
            chat_id = settings.env.telegram_debug_chat_id

        publisher = TelegramClient(bot_token=bot_token, chat_id=chat_id)
        PublishPostStep(publisher=publisher, platform=settings.run.publish.platform).execute(
            ctx,
            PublishPostInput(
                image_path=image_out.image_path,
                caption=caption_out.caption,
            ),
        )
        target = settings.run.publish.platform if publish else "debug DM"
        print(f"Published to {target}.")

    # step 5: write a summary of the run (config, run_id, dry_run flag, publish status)
    write_summary(ctx, settings.run.model_dump(), dry_run)
