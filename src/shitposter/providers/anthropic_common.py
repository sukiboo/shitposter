from shitposter.constants import (
    ANTHROPIC_ADAPTIVE_THINKING_MODELS,
    ANTHROPIC_EFFORT_LEVELS,
    ANTHROPIC_EFFORT_MODELS,
)


def validate_thinking(
    model: str, max_tokens: int, budget_tokens: int | None, effort: str | None
) -> None:
    if effort is not None:
        if effort not in ANTHROPIC_EFFORT_LEVELS:
            raise ValueError(
                f"Unsupported effort '{effort}'. "
                f"Allowed: {', '.join(sorted(ANTHROPIC_EFFORT_LEVELS))}"
            )
        if model not in ANTHROPIC_EFFORT_MODELS:
            raise ValueError(f"{model} does not support effort; omit it")
    if model in ANTHROPIC_ADAPTIVE_THINKING_MODELS:
        if budget_tokens is not None:
            raise ValueError(
                f"{model} rejects budget_tokens (removed in favour of adaptive "
                "thinking); drop it and set effort instead"
            )
    elif budget_tokens is not None:
        if budget_tokens < 1024:
            raise ValueError("budget_tokens must be at least 1024")
        if budget_tokens >= max_tokens:
            raise ValueError("max_tokens must be greater than budget_tokens")


def thinking_kwargs(model: str, budget_tokens: int | None, effort: str | None) -> dict:
    kwargs: dict = {}
    if model in ANTHROPIC_ADAPTIVE_THINKING_MODELS:
        kwargs["thinking"] = {"type": "adaptive"}
    elif budget_tokens is not None:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget_tokens}
    if effort is not None:
        kwargs["output_config"] = {"effort": effort}
    return kwargs
