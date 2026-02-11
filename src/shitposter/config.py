from __future__ import annotations

from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_settings(steps_path: Path = Path("pipelines/steps.yaml")) -> Settings:
    load_dotenv()
    return Settings(env=EnvSettings(), run=load_run_config(steps_path))


class _NoDuplicateKeysLoader(yaml.SafeLoader):
    pass


def _check_duplicate_keys(loader: yaml.Loader, node: yaml.MappingNode) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in mapping:
            raise ValueError(f"Duplicate key '{key}' in {node.start_mark}")
        mapping[key] = loader.construct_object(value_node)
    return mapping


_NoDuplicateKeysLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _check_duplicate_keys
)


def load_run_config(path: Path = Path("pipelines/steps.yaml")) -> RunConfig:
    data = yaml.load(path.read_text(), _NoDuplicateKeysLoader)  # nosec B506
    return RunConfig.model_validate(data)


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    artifacts_path: Path = Path("artifacts")
    openai_api_key: str = ""


class Settings(BaseModel):
    env: EnvSettings
    run: RunConfig


class StepConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str

    @field_validator("type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        from shitposter.steps import STEPS

        if v not in STEPS:
            raise ValueError(f"Unknown step type '{v}'. Allowed: {sorted(STEPS)}")
        return v


class RunConfig(BaseModel):
    steps: dict[str, StepConfig]
