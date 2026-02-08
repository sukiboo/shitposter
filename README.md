# shitposter

Automated content generation and posting pipeline. Generates images, builds captions, and posts to Telegram. Designed to run on a VPS with cron.

## Pipeline

1. **Prompt** — prepends "an image of" to the configured prompt
2. **Image** — generates an image from the prompt (placeholder provider for now, real provider TBD)
3. **Caption** — generates a post caption from the prompt (placeholder provider for now)
4. **Publish** — sends the image + caption to Telegram
5. **Summary** — writes a run summary (config snapshot, run ID, publish status)

Each step has pydantic-validated I/O models. Artifacts are written to a per-run directory under the configured artifact root.

## Project structure

```
src/shitposter/
  cli.py                  # typer CLI
  pipeline.py             # orchestrates steps in sequence
  config.py               # EnvSettings (.env) + RunConfig (settings.yaml)
  artifacts.py            # RunContext model + file I/O helpers

  steps/
    base.py               # Step[TInput, TOutput] ABC
    construct_prompt.py   # ConstructPromptStep
    generate_image.py     # GenerateImageStep
    generate_caption.py   # GenerateCaptionStep
    publish_post.py       # PublishPostStep

  clients/
    telegram.py           # httpx wrapper for Telegram Bot API
    text_to_image.py      # placeholder image provider (Pillow)
    text_to_text.py       # placeholder caption provider

tests/
  conftest.py
  test_artifacts.py
  test_prompt.py
  test_pipeline.py
```

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Copy the example files and fill in your values:

```bash
cp .env.example .env
cp settings.example.yaml settings.yaml
```

### `.env`

```
ARTIFACTS_PATH=./artifacts

TELEGRAM_DEBUG_BOT_TOKEN=your-debug-bot-token
TELEGRAM_DEBUG_CHAT_ID=your-debug-chat-id

TELEGRAM_CHANNEL_BOT_TOKEN=your-channel-bot-token
TELEGRAM_CHANNEL_CHAT_ID=your-channel-chat-id
```

### `settings.yaml`

```yaml
prompt:
  prompt: "a cat wearing a business suit"

image:
  provider: placeholder

caption:
  provider: placeholder

publish:
  platform: telegram
```

## Usage

```bash
# dry run (generates artifacts, skips publishing)
uv run shitposter run --dry-run

# default: generates + sends to debug DM
uv run shitposter run

# publish to channel for real
uv run shitposter run --publish

# run for a specific timestamp
uv run shitposter run --at 2026-02-08_09-00-00

# force re-run (even if already published for that run ID)
uv run shitposter run --at 2026-02-08_09-00-00 --force
```

## Run artifacts

Each run creates a directory under `<artifacts_path>/<run_id>/`:

```
2026-02-08_09-00-00/
  prompt.json
  image.png
  image_meta.json
  caption.json
  publish.json      # only if published
  summary.json
```

## Tests

```bash
uv run pytest
```

## Deployment (VPS + cron)

```bash
git clone <repo> /opt/shitposter
cd /opt/shitposter && uv sync
cp .env.example .env          # fill in tokens
cp settings.example.yaml settings.yaml
```

```cron
0 9 * * * cd /opt/shitposter && .venv/bin/shitposter run >> /var/log/shitposter.log 2>&1
```
