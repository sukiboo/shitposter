# [wip] shitposter

Automated content generation and posting pipeline. Generates images, builds captions, and posts to Telegram. Designed to run on a VPS with cron.

## Pipeline

1. **Scrape holidays** — fetches holidays from the web
2. **Choose holiday** — selects one entry from the list
3. **Prompt** — constructs the image prompt (literal string or generated via a text provider)
4. **Image** — generates an image from the prompt
5. **Caption** — generates a post caption from the prompt
6. **Publish** — sends the image + caption to configured platforms
7. **Summary** — writes a run summary (config snapshot, run ID, publish status)

Step order and config are defined in a pipeline YAML file under `configs/`. Artifacts are written to a per-run directory under the configured artifact root.

## Steps and providers

| Step | Type | Providers | Config |
|---|---|---|---|
| Scrape holidays | `scrape_holidays` | `checkiday` | `provider`, `date` |
| Choose holiday | `choose_holiday` | `placeholder`, `openai` | `provider`, `inputs`, `template` |
| Prompt | `construct_prompt` | `placeholder`, `constant`, `openai` | `prompt` (literal) or `provider` + `template` |
| Image | `generate_image` | `placeholder` (random pixels), `openai` (gpt-image-1-mini/1/1.5) | `provider`, `inputs`, `template` |
| Caption | `generate_caption` | `placeholder`, `openai` (gpt-5-nano/mini/5/5.1/5.2) | `provider`, `inputs`, `template` |
| Publish | `publish_post` | `placeholder`, `telegram` | `inputs`, `platforms` (list) |

`inputs` declares which prior step outputs this step reads from (list or comma-separated string). Templates use `{step_name}` placeholders resolved from declared inputs only.

## Project structure

```
configs/
  steps.yaml              # default pipeline config
  steps-simple.yaml       # simple config (no holiday scraping)
  steps-placeholder.yaml  # all-placeholder config for testing

src/shitposter/
  cli.py                  # typer CLI
  pipeline.py             # orchestrates steps in sequence
  config.py               # EnvSettings (.env) + RunConfig (pipeline YAML)
  artifacts.py            # RunContext + per-run directory management

  steps/
    base.py               # Step ABC + StepResult
    scrape_holidays.py    # ScrapeHolidaysStep
    choose_holiday.py     # ChooseHolidayStep
    construct_prompt.py   # ConstructPromptStep
    generate_image.py     # GenerateImageStep
    generate_caption.py   # GenerateCaptionStep
    publish_post.py       # PublishPostStep

  providers/
    base.py               # provider ABCs + auto-registration via __init_subclass__
    web_to_context.py     # context providers (checkiday)
    text_to_int.py        # text-to-int providers (placeholder, openai)
    text_to_text.py       # text providers (placeholder, constant, openai)
    text_to_image.py      # image providers (placeholder, openai)
    publishers.py         # publishing providers (placeholder, telegram)

tests/
```

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Copy the example `.env` and fill in your values:

```bash
cp .env.example .env
```

### `.env`

```
ARTIFACTS_PATH=./artifacts
OPENAI_API_KEY=your-openai-api-key

TELEGRAM_DEBUG_BOT_TOKEN=your-debug-bot-token
TELEGRAM_DEBUG_CHAT_ID=your-debug-chat-id

TELEGRAM_CHANNEL_BOT_TOKEN=your-channel-bot-token
TELEGRAM_CHANNEL_CHAT_ID=your-channel-chat-id
```

### Pipeline config

Pipeline configs live in `configs/`. Example (`configs/steps-simple.yaml`):

```yaml
steps:
  prompt:
    type: construct_prompt
    provider: constant
    prompt: "a cat wearing a business suit"

  image:
    type: generate_image
    provider: openai
    inputs: prompt
    template: "Generate an image of {prompt}."

  caption:
    type: generate_caption
    provider: openai
    inputs: prompt
    template: "Generate a funny caption (use emoji!) for an image of {prompt}. Your answer must be a single caption, nothing else."

  publish:
    type: publish_post
    inputs: image, caption
    platforms:
      - telegram
```

## Usage

```bash
# dry run (generates artifacts, skips publishing)
uv run shitposter run --dry-run

# default: generates + sends to debug DM
uv run shitposter run

# publish to specified platforms
uv run shitposter run --publish

# use a different pipeline config (loads configs/steps-new.yaml)
uv run shitposter run -s steps-new

# run for a specific timestamp
uv run shitposter run --at 2026-02-08_09-00-00

# force re-run (even if already published for that run ID)
uv run shitposter run --at 2026-02-08_09-00-00 --force
```

## Run artifacts

Each run creates a directory under `<artifacts_path>/<run_id>/`:

```
2026-02-08_09-00-00/
  0_holidays.json
  1_holiday.json
  2_prompt.json
  image.png
  3_image.json
  4_caption.json
  5_publish.json
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
cp .env.example .env
```

```cron
0 9 * * * cd /opt/shitposter && .venv/bin/shitposter run >> /var/log/shitposter.log 2>&1
```
