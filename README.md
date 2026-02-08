# shitposter

Automated content generation and posting pipeline. Generates images, builds captions, and posts to Telegram. Designed to run on a VPS with cron.

## Pipeline

1. **Prompt** — picks a random topic from a configured list and expands it into an image-generation prompt
2. **Image** — generates an image from the prompt (placeholder provider for now, real provider TBD)
3. **Caption** — builds a post caption from the topic and a template
4. **Publish** — sends the image + caption to Telegram
5. **Manifest** — writes a run summary (config snapshot, run ID, publish status)

Each step has pydantic-validated I/O models. Artifacts are written to a per-run directory under the configured artifact root.

## Project structure

```
src/shitposter/
  cli.py              # typer CLI
  pipeline.py         # orchestrates steps in sequence
  config.py           # EnvSettings (.env) + AppConfig (settings.yaml)
  artifacts.py        # RunContext model + file I/O helpers

  steps/
    base.py           # Step[TInput, TOutput] ABC
    prompt.py         # PromptStep
    image.py          # ImageStep + image provider protocol
    caption.py        # CaptionStep
    publish.py        # PublishStep + publisher protocol

  clients/
    telegram.py       # httpx wrapper for Telegram Bot API
    image_api.py      # placeholder image provider (Pillow)

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
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
SHITPOSTER_ARTIFACT_ROOT=./artifacts
```

### `settings.yaml`

```yaml
prompt:
  template: "A surreal digital painting of {topic}, vibrant colors, dreamlike atmosphere"
  topics:
    - "a cat wearing a business suit"
    - "a frog contemplating existence"

image:
  provider: placeholder
  width: 1024
  height: 1024

caption:
  template: "{topic} | AI-generated art"

publish:
  platform: telegram
```

## Usage

```bash
# dry run (generates artifacts, skips publishing)
uv run shitposter run --dry-run

# publish to telegram
uv run shitposter run

# run for a specific timestamp
uv run shitposter run --at 2026-02-08_09-00-00

# force re-run (even if already published for that run ID)
uv run shitposter run --at 2026-02-08_09-00-00 --force
```

## Run artifacts

Each run creates a directory under `<artifact_root>/runs/<run_id>/`:

```
2026-02-08_09-00-00/
  prompt.txt
  prompt.json
  image.png
  image_meta.json
  caption.txt
  publish.json      # only if published
  manifest.json
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
