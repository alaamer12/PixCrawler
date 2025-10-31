from pathlib import Path
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

FormatLiteral = Literal["webp", "avif", "png", "jxl"]
ArchiveTypeLiteral = Literal["zstd", "zip", "none"]


class ArchiveSettings(BaseSettings):
    enable: bool = Field(default=True)
    tar: bool = Field(default=True)
    type: ArchiveTypeLiteral = Field(default="zstd")
    level: int = Field(default=10)
    output: Path = Field(default=Path("./dataset.zst"))

    @field_validator("level")
    @classmethod
    def _validate_level(cls, v: int) -> int:
        if v < 1 or v > 19:
            raise ValueError("archive.level must be between 1 and 19")
        return v


class CompressionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    input_dir: Path = Field(default=Path("./images"))
    output_dir: Path = Field(default=Path("./compressed"))
    format: FormatLiteral = Field(default="webp")
    quality: int = Field(default=85)
    lossless: bool = Field(default=False)
    workers: int = Field(default=0)
    archive__enable: Optional[bool] = Field(default=None)
    archive__tar: Optional[bool] = Field(default=None)
    archive__type: Optional[ArchiveTypeLiteral] = Field(default=None)
    archive__level: Optional[int] = Field(default=None)
    archive__output: Optional[Path] = Field(default=None)

    def archive(self) -> ArchiveSettings:
        base = ArchiveSettings()
        if self.archive__enable is not None:
            base.enable = self.archive__enable
        if self.archive__tar is not None:
            base.tar = self.archive__tar
        if self.archive__type is not None:
            base.type = self.archive__type
        if self.archive__level is not None:
            base.level = self.archive__level
        if self.archive__output is not None:
            base.output = self.archive__output
        return base

    @field_validator("quality")
    @classmethod
    def _validate_quality(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("quality must be between 0 and 100")
        return v

    def resolved_workers(self) -> int:
        import os
        if self.workers and self.workers > 0:
            return self.workers
        try:
            return max(1, os.cpu_count() or 1)
        except Exception:
            return 1
