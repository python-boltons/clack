"""Contains the base configuration class for clack."""

from __future__ import annotations

from typing import List, Protocol, Sequence, Type, TypeVar, runtime_checkable

from logrus import Log
from pydantic import BaseSettings


ConfigType = TypeVar("ConfigType", bound="AbstractConfig", covariant=True)


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


class Config(BaseSettings, allow_mutation=False):
    """Default CLI arguments / app configuration."""

    logs: List[Log]
    verbose: int
