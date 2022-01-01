"""Contains the base configuration class for clack."""

from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    MutableMapping,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
)

from logrus import Log
from pydantic import BaseSettings
from pydantic.fields import ModelField
from typist import PathLike
import yaml

from . import xdg


Config_T = TypeVar("Config_T", bound="AbstractConfig", covariant=True)

_SettingsSource = Callable[[BaseSettings], Dict[str, Any]]


@runtime_checkable
class AbstractConfig(Protocol[Config_T]):
    """Application Configuration Protocol

    In other words, this class describes what an application Config object
    should look like.
    """

    __fields__: Dict[str, ModelField]

    @classmethod
    def from_cli_args(cls: Type[Config_T], argv: Sequence[str]) -> Config_T:
        """Constructs a new Config object from command-line arguments."""


class Config(BaseSettings):
    """Default CLI arguments / app configuration."""

    logs: List[Log] = []
    verbose: int = 0

    class Config:
        """Pydantic BaseSettings Configuration."""

        allow_mutation = False

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

    class MutexGroup:
        def __init__(self, config_paths: List[Path]):
            self.config_paths = config_paths

        @classmethod
        def from_paths(
            cls, *path_like_list: Union[PathLike, List[PathLike]]
        ) -> "MutexGroup":
            new_path_like_list = []
            for x in path_like_list:
                if isinstance(x, list):
                    for y in x:
                        new_path_like_list.append(y)
                else:
                    new_path_like_list.append(x)
            return cls([Path(p) for p in new_path_like_list])

        def bind(
            self, *extras: Union[PathLike, List[PathLike]]
        ) -> "MutexGroup":
            new_extras = []
            for x in extras:
                if isinstance(x, list):
                    for y in x:
                        new_extras.append(y)
                else:
                    new_extras.append(x)

            return MutexGroup(
                self.config_paths + [Path(p) for p in new_extras]
            )

    def all_yamls(name: PathLike) -> List[PathLike]:
        name = str(name)
        return [name + ".yml", name + ".yaml"]

    def populate_result_from_mgroup(
        mut_result_map: MutableMapping[str, Any], mgroup: MutexGroup
    ) -> None:
        for config_path in mgroup.config_paths:
            if config_path.is_file():
                yaml_dict = yaml.load(
                    config_path.read_bytes(), yaml.SafeLoader
                )
                mut_result_map.update(yaml_dict)
                break

    def config_settings(settings: BaseSettings) -> Dict[str, Any]:
        del settings

        result: Dict[str, Any] = {}
        app_path = Path(app_name)
        hidden_app_path = Path("." + app_name)

        full_xdg_dir = xdg.get_full_dir("config", app_name)
        xdg_group = MutexGroup.from_paths(
            all_yamls(full_xdg_dir / app_name),
            all_yamls(full_xdg_dir / "config"),
        )

        populate_result_from_mgroup(result, xdg_group)

        local_group = MutexGroup.from_paths(
            all_yamls(app_path),
            all_yamls(app_path / app_name),
            all_yamls(app_path / "config"),
            all_yamls(hidden_app_path / app_name),
            all_yamls(hidden_app_path / "config"),
        )
        populate_result_from_mgroup(result, local_group)

        return result

    return config_settings
