OPENAI_EFFORT_LEVELS = {"none", "low", "medium", "high"}

OPENAI_TEXT_MODELS = {
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-5",
    "gpt-5.1",
    "gpt-5.2",
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-5.4",
    "gpt-5.5",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
}

ANTHROPIC_EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}

ANTHROPIC_TEXT_MODELS = {
    "claude-opus-5",
    "claude-opus-4-8",
    "claude-opus-4-6",
    "claude-sonnet-5",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-haiku-4-5-20251001",
}

# budget_tokens was removed on these models: they reject it with a 400 and take
# thinking={"type": "adaptive"} instead, with depth controlled by output_config.effort.
ANTHROPIC_ADAPTIVE_THINKING_MODELS = {
    "claude-opus-5",
    "claude-opus-4-8",
    "claude-sonnet-5",
}

# output_config.effort errors on Haiku 4.5, so it is sent only for these models.
ANTHROPIC_EFFORT_MODELS = ANTHROPIC_ADAPTIVE_THINKING_MODELS | {
    "claude-opus-4-6",
    "claude-sonnet-4-6",
}
