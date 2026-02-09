from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_settings() -> Settings:
    return Settings(env=EnvSettings(), run=load_run_config())


def load_run_config(path: Path = Path("settings.yaml")) -> RunConfig:
    data = yaml.safe_load(path.read_text())
    return RunConfig.model_validate(data)


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    artifacts_path: Path = Path("artifacts")
    telegram_debug_bot_token: str = ""
    telegram_debug_chat_id: str = ""
    telegram_channel_bot_token: str = ""
    telegram_channel_chat_id: str = ""
    openai_api_key: str = ""


class Settings(BaseModel):
    env: EnvSettings
    run: RunConfig


class RunConfig(BaseModel):
    prompt: PromptConfig
    image: ImageConfig
    caption: CaptionConfig
    publish: PublishConfig


class PromptConfig(BaseModel):
    prompt: str


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    provider: str


class ImageConfig(ProviderConfig):
    @field_validator("provider")
    @classmethod
    def _check_provider(cls, v: str) -> str:
        from shitposter.clients.text_to_image import PROVIDERS

        if v not in PROVIDERS:
            raise ValueError(f"Unknown provider '{v}'. Allowed: {sorted(PROVIDERS)}")
        return v


class CaptionConfig(ProviderConfig):
    @field_validator("provider")
    @classmethod
    def _check_provider(cls, v: str) -> str:
        from shitposter.clients.text_to_text import PROVIDERS

        if v not in PROVIDERS:
            raise ValueError(f"Unknown provider '{v}'. Allowed: {sorted(PROVIDERS)}")
        return v


class PublishConfig(BaseModel):
    platform: str
