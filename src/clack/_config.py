"""Contains the base configuration class for clack."""

from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    runtime_checkable,
)

from logrus import Log
from pydantic import BaseSettings
from pydantic.fields import ModelField
import yaml

from . import xdg


ConfigType = TypeVar("ConfigType", bound="AbstractConfig", covariant=True)

_SettingsSource = Callable[[BaseSettings], Dict[str, Any]]


@runtime_checkable
class AbstractConfig(Protocol[ConfigType]):
    """Application Configuration Protocol

    In other words, this class describes what an application Config object
    should look like.
    """

    __fields__: Dict[str, ModelField]

    @classmethod
    def from_cli_args(
        cls: Type[ConfigType], argv: Sequence[str]
    ) -> ConfigType:
        """Constructs a new Config object from command-line arguments."""


class Config(BaseSettings):
    """Default CLI arguments / app configuration."""

    logs: List[Log] = []
    verbose: int = 0

    class Config:
        """Pydantic BaseSettings Configuration."""

        allow_mutation = False
        env_file = ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: _SettingsSource,
            env_settings: _SettingsSource,
            file_secret_settings: _SettingsSource,
        ) -> Tuple[_SettingsSource, ...]:
            """Customize where we load our application config from."""
            # HACK: Use nested import to prevent circular import errors.
            from ._dynvars import get_app_name

            del file_secret_settings

            app_name = get_app_name()
            return (
                init_settings,
                env_settings,
                _config_settings_factory(app_name),
            )


def _config_settings_factory(app_name: str) -> _SettingsSource:
    """Configuration Settings Factory Function

    Factory function that returns a pydantic.BaseSettings source callable that
    reads values from a YAML config file.
    """

    def config_settings(settings: BaseSettings) -> Dict[str, Any]:
        del settings

        all_config_files: List[Path] = []
        all_basenames = [app_name + ".yml", app_name + ".yaml"]

        full_xdg_dir = xdg.get_full_dir("config", app_name)
        for basename in all_basenames:
            fullname = full_xdg_dir / basename
            all_config_files.append(fullname)

        for basename in all_basenames:
            all_config_files.append(Path(basename))

        result = {}
        for config_file in all_config_files:
            if config_file.is_file():
                yaml_dict = yaml.load(
                    config_file.read_bytes(), yaml.SafeLoader
                )
                result.update(yaml_dict)

        return result

    return config_settings
