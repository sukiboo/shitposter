from __future__ import annotations

from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_settings(steps_path: Path = Path("configs/steps.yaml")) -> Settings:
    load_dotenv(override=True)
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


def _make_loader(config_dir: Path) -> type[yaml.SafeLoader]:
    class _Loader(_NoDuplicateKeysLoader):
        pass

    def _file_constructor(loader: yaml.Loader, node: yaml.ScalarNode) -> str:
        return (config_dir / loader.construct_scalar(node)).read_text().strip()

    _Loader.add_constructor("!file", _file_constructor)
    return _Loader


def load_run_config(path: Path = Path("configs/steps.yaml")) -> RunConfig:
    loader = _make_loader(path.parent)
    data = yaml.load(path.read_text(), loader)  # nosec B506
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
    inputs: list[str] = []

    @field_validator("type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        from shitposter.steps import STEPS

        if v not in STEPS:
            raise ValueError(f"Unknown step type '{v}'. Allowed: {sorted(STEPS)}")
        return v

    @field_validator("inputs", mode="before")
    @classmethod
    def _parse_inputs(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @model_validator(mode="after")
    def _validate_step_config(self) -> "StepConfig":
        from shitposter.steps import STEPS

        step_cls = STEPS[self.type]
        step_cls.validate_config(self.model_dump(exclude={"type", "inputs"}))
        return self


class RunConfig(BaseModel):
    steps: dict[str, StepConfig]

    @model_validator(mode="after")
    def _validate_input_refs(self) -> "RunConfig":
        seen: set[str] = set()
        for key, step in self.steps.items():
            for inp in step.inputs:
                if inp not in seen:
                    raise ValueError(
                        f"Step '{key}' references input '{inp}' "
                        f"which is not a previously defined step"
                    )
            seen.add(key)
        return self
