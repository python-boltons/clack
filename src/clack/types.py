"""Shared types live here."""

from __future__ import annotations

from pathlib import Path
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
)

from eris import ErisError, Result
from pydantic.fields import ModelField
from typist import PathLike


ClackParser = Callable[[Sequence[str]], Dict[str, Any]]
ClackRunner = Callable[["Config_T"], int]
ConfigFile_T = TypeVar("ConfigFile_T", bound="ClackConfigFile")
Config_T = TypeVar("Config_T", bound="ClackConfig")


@runtime_checkable
class ClackConfig(Protocol):
    """Application Configuration Protocol

    In other words, this class describes what an application Config object
    should look like.
    """

    __fields__: Dict[str, ModelField]

    @classmethod
    def from_cli_args(cls: Type[Config_T], argv: Sequence[str]) -> Config_T:
        """Constructs a new Config object from command-line arguments."""


@runtime_checkable
class ClackConfigFile(Protocol):
    """The protocol used for configuration file classes."""

    # All possible filename extensions for this type of config file.
    extensions: List[str]
    path: Path

    def __init__(self, path: PathLike) -> None:
        pass

    def get(self, key: str) -> Result[Any, ErisError]:
        """Getter for values in this config file."""

    @classmethod
    def new(
        cls: Type[ConfigFile_T], path: PathLike, **kwargs: Any
    ) -> ConfigFile_T:
        """Construct a new ClackConfigFile object."""

    def set(
        self, key: str, value: Any, *, allow_new: bool = False
    ) -> Result[Any, ErisError]:
        """Setter for values in this config file."""

    def to_dict(self) -> Result[dict[str, Any], ErisError]:
        """Converts this configuration file into a dict."""


class ClackMain(Protocol):
    """Type of the `main()` function returned by `main_factory()`."""

    def __call__(self, argv: Sequence[str] = None) -> int:
        """This method captures the `main()` function's signature."""
