"""Contains the base configuration class for clack."""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    runtime_checkable,
    Tuple,
)

from logrus import Log
from pydantic import BaseSettings


ConfigType = TypeVar("ConfigType", bound="AbstractConfig", covariant=True)

_SettingsSource = Callable[[BaseSettings], Dict[str, Any]]


@runtime_checkable
class AbstractConfig(Protocol[ConfigType]):
    """Application Configuration Protocol

    In other words, his class describes what an application Config object
    should look like.
    """

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
            del file_secret_settings
            return (init_settings, env_settings, _config_file_settings)


def _config_file_settings(settings: BaseSettings) -> Dict[str, Any]:
    pass
