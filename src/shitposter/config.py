from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    shitposter_artifact_root: Path = Path("artifacts")


class PromptConfig(BaseModel):
    template: str = "A surreal digital painting of {topic}"
    topics: list[str] = ["a cat"]


class ImageConfig(BaseModel):
    provider: str = "placeholder"
    width: int = 1024
    height: int = 1024


class CaptionConfig(BaseModel):
    template: str = "{topic}"


class PublishConfig(BaseModel):
    platform: str = "telegram"


class AppConfig(BaseModel):
    prompt: PromptConfig = PromptConfig()
    image: ImageConfig = ImageConfig()
    caption: CaptionConfig = CaptionConfig()
    publish: PublishConfig = PublishConfig()


class Settings(BaseModel):
    env: EnvSettings
    app: AppConfig


def load_app_config(path: Path = Path("settings.yaml")) -> AppConfig:
    if path.exists():
        data = yaml.safe_load(path.read_text())
        return AppConfig.model_validate(data or {})
    return AppConfig()


def load_settings() -> Settings:
    return Settings(env=EnvSettings(), app=load_app_config())
