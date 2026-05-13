from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("config.ini")


@dataclass(frozen=True)
class AppConfig:
    project_name: str
    version: str


@dataclass(frozen=True)
class DataConfig:
    test_size: float
    random_state: int
    drop_duplicates: bool


@dataclass(frozen=True)
class ModelConfig:
    model_type: str
    n_estimators: int
    max_depth: int | None
    min_samples_split: int


@dataclass(frozen=True)
class Settings:
    app: AppConfig
    data: DataConfig
    model: ModelConfig


def _parse_optional_int(value: str) -> int | None:
    normalized = value.strip().lower()
    if normalized in {"", "none", "null"}:
        return None
    return int(normalized)


def load_settings(config_path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    parser = ConfigParser()
    parsed_files = parser.read(Path(config_path), encoding="utf-8")

    if not parsed_files:
        raise FileNotFoundError(f"Config file was not found: {config_path}")

    return Settings(
        app=AppConfig(
            project_name=parser.get("app", "project_name"),
            version=parser.get("app", "version"),
        ),
        data=DataConfig(
            test_size=parser.getfloat("data", "test_size"),
            random_state=parser.getint("data", "random_state"),
            drop_duplicates=parser.getboolean("data", "drop_duplicates"),
        ),
        model=ModelConfig(
            model_type=parser.get("model", "model_type"),
            n_estimators=parser.getint("model", "n_estimators"),
            max_depth=_parse_optional_int(parser.get("model", "max_depth")),
            min_samples_split=parser.getint("model", "min_samples_split"),
        ),
    )
