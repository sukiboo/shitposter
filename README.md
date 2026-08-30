# shitposter

Automated content generation and posting pipeline. Generates images, builds captions, and posts to configured social platforms. Designed to run on a VPS with a systemd timer.

Currently posting to
- Telegram: [Cat Slop Daily](https://t.me/catslopdaily)
- Twitter/X: [@CatSlopDaily](https://x.com/CatSlopDaily)


## Pipeline

1. **Resolve date** — determines the target date (today or override)
2. **Retrieve holidays** — fetches holidays for that date
3. **Choose holiday** — selects an entry while considering the previous 14 published choices, including recent category use
4. **Generate prompt** — uses the holiday and recent prompt history to create a minimal, single-joke image prompt
5. **Generate image** — generates an image from the prompt
6. **Select emojis** — chooses holiday-specific header emojis while softly preferring choices not used recently
7. **Construct header** — composes `date — holiday emojis`
8. **Generate caption** — adds a short second comedic beat using recent captions and emoji choices as diversity context
9. **Publish** — sends the image and caption to configured platforms
10. **Summary** — records the run ID, status, and metadata for every step

History steps read outputs from previously published run summaries. Their recency rules are soft preferences: relevance and content quality still take priority over novelty. Step order and configuration are defined in a pipeline YAML file under `configs/`. Artifacts are written to a per-run directory under the configured artifact root.

## Steps and providers

| Step | Type | Providers | Config |
|---|---|---|---|
| Resolve date | `resolve_date` | `date` | `provider`, `value` |
| Retrieve holidays | `retrieve_holidays` | `checkiday`, `checkiday_api`, `checkiday_scrape` | `provider`, `inputs` |
| Retrieve history | `retrieve_history` | — (reads past run summaries) | `step`, `runs` |
| Choose holiday | `choose_holiday` | `placeholder`, `openai`, `anthropic` | `provider`, `inputs`, `template` |
| Select emojis | `select_emojis` | `placeholder`, `openai`, `anthropic` | `provider`, `inputs`, `template` |
| Generate text | `generate_text` | `placeholder`, `constant`, `openai`, `anthropic` | `provider`, `inputs`, `template` |
| Generate caption | `generate_caption` | `placeholder`, `openai`, `anthropic` | `provider`, `inputs`, `template` |
| Generate image | `generate_image` | `placeholder` (random pixels), `openai` (gpt-image-1-mini/1/1.5/2) | `provider`, `inputs`, `template` |
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
    retrieve_history.py   # RetrieveHistoryStep
    retrieve_holidays.py  # RetrieveHolidaysStep
    choose_holiday.py     # ChooseHolidayStep
    select_emojis.py      # SelectEmojisStep
    generate_text.py      # GenerateTextStep + GenerateCaptionStep
    generate_image.py     # GenerateImageStep
    publish_post.py       # PublishPostStep

  providers/
    base.py               # provider ABCs + auto-registration via __init_subclass__
    text_to_date.py       # date providers (date)
    web_to_context.py     # context providers (checkiday API, checkiday_scrape)
    text_to_int.py        # text-to-int providers (placeholder, openai, anthropic)
    text_to_emoji.py      # text-to-emoji providers (placeholder, openai, anthropic)
    text_to_text.py       # text providers (placeholder, constant, openai, anthropic)
    text_to_caption.py    # caption providers (placeholder, openai, anthropic) — structured output
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
ANTHROPIC_API_KEY=your-anthropic-api-key
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
2026-08-30_10-15-54/
  0_date.json
  1_holiday_list.json
  2_holiday_history.json
  3_holiday.json
  4_prompt_history.json
  5_prompt.json
  6_image.json
  7_header_emoji_history.json
  8_header_emojis.json
  9_caption_header.json
  10_caption_history.json
  11_caption_body.json
  12_caption.json
  13_publish.json
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
