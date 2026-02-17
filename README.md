# shitposter

Automated content generation and posting pipeline. Generates images, builds captions, and posts to Telegram. Designed to run on a VPS with a systemd timer.

Currently posting to
- Telegram: [Cat Slop Daily](https://t.me/catslopdaily)
- Twitter/X: [@CatSlopDaily](https://x.com/CatSlopDaily)


## Pipeline

1. **Resolve date** — determines the target date (today or override)
2. **Retrieve holidays** — fetches holidays via API for that date
3. **Choose holiday** — selects one entry from the list
4. **Construct header** — builds a formatted header line with emoji
5. **Generate prompt** — generates a relevant image prompt
6. **Generate image** — generates an image from the prompt
7. **Generate caption** — generates a structured caption (50-350 chars)
8. **Publish** — sends the image + caption to configured platforms
9. **Summary** — writes a run summary (config snapshot, run ID, publish status)

Step order and config are defined in a pipeline YAML file under `configs/`. Artifacts are written to a per-run directory under the configured artifact root.

## Steps and providers

| Step | Type | Providers | Config |
|---|---|---|---|
| Resolve date | `resolve_date` | `date` | `provider`, `value` |
| Retrieve holidays | `retrieve_holidays` | `checkiday`, `checkiday_scrape` | `provider`, `inputs` |
| Choose holiday | `choose_holiday` | `placeholder`, `openai` | `provider`, `inputs`, `template` |
| Construct header | `construct_header` | `placeholder`, `openai` | `provider`, `inputs`, `template` |
| Generate text | `generate_text` | `placeholder`, `constant`, `openai` | `provider`, `inputs`, `template` |
| Generate caption | `generate_caption` | `placeholder`, `openai` | `provider`, `inputs`, `template` |
| Generate image | `generate_image` | `placeholder` (random pixels), `openai` (gpt-image-1-mini/1/1.5) | `provider`, `inputs`, `template` |
| Publish | `publish_post` | `placeholder`, `telegram`, `debug`, `twitter` | `inputs`, `platforms` (list) |

`inputs` declares which prior step outputs this step reads from (list or comma-separated string). Templates use `{step_name}` placeholders resolved from declared inputs only.

## Project structure

```
configs/
  dev.yaml                # default pipeline config (holiday pipeline)
  holiday.yaml            # production holiday pipeline
  simple.yaml             # simple config (no holiday scraping)
  placeholder.yaml        # all-placeholder config for testing

src/shitposter/
  cli.py                  # typer CLI
  pipeline.py             # orchestrates steps in sequence
  config.py               # EnvSettings (.env) + RunConfig (pipeline YAML)
  artifacts.py            # RunContext + per-run directory management

  steps/
    base.py               # Step ABC + StepResult
    resolve_date.py       # ResolveDateStep
    retrieve_holidays.py  # RetrieveHolidaysStep
    choose_holiday.py     # ChooseHolidayStep
    construct_header.py   # ConstructHeaderStep
    generate_text.py      # GenerateTextStep + GenerateCaptionStep
    generate_image.py     # GenerateImageStep
    publish_post.py       # PublishPostStep

  providers/
    base.py               # provider ABCs + auto-registration via __init_subclass__
    text_to_date.py       # date providers (date)
    web_to_context.py     # context providers (checkiday API, checkiday_scrape)
    text_to_int.py        # text-to-int providers (placeholder, openai)
    text_to_emoji.py      # text-to-emoji providers (placeholder, openai)
    text_to_text.py       # text providers (placeholder, constant, openai)
    text_to_caption.py    # caption providers (placeholder, openai) — structured output
    text_to_image.py      # image providers (placeholder, openai)
    publishers.py         # publishing providers (placeholder, telegram, debug, twitter)

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
# Deployment
SERVER_USER=your-username
SERVER_HOST=your-hostname
SERVER_PATH=~/apps/shitposter
REPO_URL=https://github.com/sukiboo/shitposter.git
STEPS_CONFIG=dev
RUN_SCHEDULE="*-*-* 08:00:00"
RUN_TIMEZONE=America/New_York

# Services
ARTIFACTS_PATH=./artifacts
CHECKIDAY_API_KEY=your-checkiday-api-key
OPENAI_API_KEY=your-openai-api-key
TELEGRAM_DEBUG_BOT_TOKEN=your-debug-bot-token
TELEGRAM_DEBUG_CHAT_ID=your-debug-chat-id
TELEGRAM_CHANNEL_BOT_TOKEN=your-channel-bot-token
TELEGRAM_CHANNEL_CHAT_ID=your-channel-chat-id
TWITTER_CONSUMER_KEY=your-twitter-consumer-key
TWITTER_CONSUMER_SECRET=your-twitter-consumer-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret
```

### Pipeline config

Pipeline configs live in `configs/`. Example (`configs/simple.yaml`):

```yaml
steps:
  prompt:
    type: generate_text
    provider: constant
    prompt: "a black cat wearing a business suit"

  image:
    type: generate_image
    provider: openai
    inputs: prompt
    template: "Generate an image of {prompt}."

  caption:
    type: generate_caption
    provider: openai
    inputs: prompt
    template: "Generate a funny caption (use emoji!) for an image of {prompt}."

  publish:
    type: publish_post
    inputs: image, caption
    platforms:
      - debug
```

## Usage

```bash
# dry run (generate artifacts, skip publishing)
uv run shitposter run --dry-run

# default: generate + publish to listed platforms
uv run shitposter run

# use a different pipeline config (load configs/simple.yaml)
uv run shitposter run -s simple
```

## Run artifacts

Each run creates a directory under `<artifacts_path>/<run_id>/`:

```
2026-02-08_09-00-00/
  0_date.json
  1_holiday_list.json
  2_holiday.json
  3_prompt.json
  4_image.json
  5_caption_header.json
  6_caption_body.json
  7_caption.json
  8_publish.json
  image.png
  summary.json
```

## Tests

```bash
uv run pytest
```

## Deployment

The pipeline runs on a VPS via a systemd user timer. All deploy config is read from `.env`.

```bash
# first-time setup + all subsequent deploys
./deploy/run.sh
```

This will:
- Install `uv` on the server if missing
- Clone the repo (first run) or `git pull --ff-only` (subsequent runs)
- Install dependencies (`uv sync --no-dev`)
- Copy `.env` to the server
- Install and enable the systemd timer

### Checking status

```bash
ssh user@host 'systemctl --user status shitposter.timer'
ssh user@host 'systemctl --user list-timers'
ssh user@host 'journalctl --user -u shitposter.service -n 50'
```
