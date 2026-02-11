# shitposter

Automated content generation and posting pipeline. Generates images, builds captions, and posts to Telegram. Designed to run on a VPS with cron.

## Pipeline

1. **Prompt** — sets the prompt (literal string or generated via a text provider)
2. **Image** — generates an image from the prompt
3. **Caption** — generates a post caption from the prompt
4. **Publish** — sends the image + caption to configured platforms
5. **Summary** — writes a run summary (config snapshot, run ID, publish status)

Step order and config are defined in a pipeline YAML file under `pipelines/`. Artifacts are written to a per-run directory under the configured artifact root.

## Steps and providers

| Step | Type | Providers | Config |
|---|---|---|---|
| Prompt | `set_prompt` | `placeholder`, `openai` | `prompt` (literal) or `provider` + `template` |
| Image | `generate_image` | `placeholder` (random pixels), `openai` (gpt-image-1-mini/1/1.5) | `provider`, `template` |
| Caption | `generate_caption` | `placeholder`, `openai` (gpt-5-nano/mini/5/5.1/5.2) | `provider`, `template` |
| Publish | `publish_post` | `placeholder`, `telegram` | `platforms` (list) |

Templates support `{prompt}` interpolation (and any other keys in the run context state).

## Project structure

```
pipelines/
  steps.yaml              # default pipeline config
  steps-placeholder.yaml  # example config (placeholder providers)

src/shitposter/
  cli.py                  # typer CLI
  pipeline.py             # orchestrates steps in sequence
  config.py               # EnvSettings (.env) + RunConfig (pipeline YAML)
  artifacts.py            # RunContext + per-run directory management

  steps/
    base.py               # Step ABC + StepResult
    set_prompt.py         # SetPromptStep
    generate_image.py     # GenerateImageStep
    generate_caption.py   # GenerateCaptionStep
    publish_post.py       # PublishPostStep

  clients/
    base.py               # provider ABCs
    text_to_text.py       # text providers (placeholder, openai)
    text_to_image.py      # image providers (placeholder, openai)
    publishers.py         # publishing providers (placeholder, telegram)

tests/
```

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Copy the example files and fill in your values:

```bash
cp .env.example .env
cp pipelines/steps.example.yaml pipelines/steps.yaml
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

Pipeline configs live in `pipelines/`. Example (`pipelines/steps.yaml`):

```yaml
steps:
  prompt:
    type: set_prompt
    prompt: "a cat wearing a business suit"

  image:
    type: generate_image
    provider: openai
    template: "Generate an image of {prompt}."

  caption:
    type: generate_caption
    provider: openai
    template: "Generate a funny caption for an image of {prompt}."

  publish:
    type: publish_post
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

# use a different pipeline config (loads pipelines/steps-new.yaml)
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
  prompt.json
  image.png
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
cp .env.example .env
cp pipelines/steps.example.yaml pipelines/steps.yaml
```

```cron
0 9 * * * cd /opt/shitposter && .venv/bin/shitposter run >> /var/log/shitposter.log 2>&1
```
