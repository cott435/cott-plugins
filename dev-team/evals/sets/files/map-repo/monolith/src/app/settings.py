"""Settings shared by every stage, from the environment with prefix `APP_`."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    export_dir: Path = Path("./exports")
    report_dir: Path = Path("./reports")
    min_rows: int = 10
