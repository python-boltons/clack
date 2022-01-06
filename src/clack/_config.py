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
    runtime_checkable,
)

from logrus import Log
from pydantic import BaseSettings
from pydantic.fields import ModelField
from typist import PathLike
import yaml

from . import xdg


Config_T = TypeVar("Config_T", bound="AbstractConfig")
co_Config_T = TypeVar("co_Config_T", bound="AbstractConfig", covariant=True)

_SettingsSource = Callable[[BaseSettings], Dict[str, Any]]


@runtime_checkable
class AbstractConfig(Protocol[co_Config_T]):
    """Application Configuration Protocol

    In other words, this class describes what an application Config object
    should look like.
    """

    __fields__: Dict[str, ModelField]

    @classmethod
    def from_cli_args(
        cls: Type[co_Config_T], argv: Sequence[str]
    ) -> co_Config_T:
        """Constructs a new Config object from command-line arguments."""


class Config(BaseSettings):
    """Default CLI arguments / app configuration."""

    logs: List[Log] = []
    verbose: int = 0

    class Config:
        """Pydantic BaseSettings Configuration."""

        allow_mutation = False
        extra = "ignore"

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

    class MutexConfigGroup:
        """Mutually Exclusive Configuration File Group.

        A single MutexConfigGroup object specifies one or more configuration
        file locations. We will ONLY load configuration values from the FIRST
        configuration file in this group that exists on disk (if any do).
        """

        def __init__(self, config_paths: List[Path]):
            self.config_paths = config_paths

        @classmethod
        def from_path_lists(
            cls, *path_like_lists: List[PathLike]
        ) -> "MutexConfigGroup":
            """MutexConfigGroup class constructor.

            Given N lists of config file paths, construct a new
            MutexConfigGroup object.
            """
            flat_path_list = []
            for path_like_list in path_like_lists:
                for path_like in path_like_list:
                    flat_path_list.append(Path(path_like))
            return cls(flat_path_list)

        def populate_config_map(
            self, mut_config_map: MutableMapping[str, Any]
        ) -> None:
            """Populate values for a config mapping using this mutex group.

            Set configuration options (by adding keys to the ``mut_config_map``
            mapping) using (at most) one of the config files corresponding with
            the ``mgroup`` MutexConfigGroup.
            """
            for config_path in self.config_paths:
                if config_path.is_file():
                    yaml_dict = yaml.safe_load(config_path.read_bytes())
                    mut_config_map.update(yaml_dict)
                    break

    def all_yamls(name: PathLike) -> List[PathLike]:
        """Helper function that adds support for all YAML filename exts."""
        name = str(name)
        return [name + ".yml", name + ".yaml"]

    def config_settings(settings: BaseSettings) -> Dict[str, Any]:
        """The pydantic.BaseSettings source callable that we will return."""
        del settings

        ##### Helper variables used by MutexConfigGroup objects...
        app_path = Path(app_name)
        base_xdg_dir = xdg.get_base_dir("config")
        clack_xdg_dir = base_xdg_dir / "clack"
        clack_apps_dir = clack_xdg_dir / "apps"
        full_xdg_dir = xdg.get_full_dir("config", app_name)
        hidden_app_path = Path("." + app_name)

        ##### MutexConfigGroup variable definitions...
        # user config files used by ALL clack apps
        #
        # e.g. ~/.config/clack/global.yml OR ~/.config/clack/apps/all.yml...
        user_group_for_all_apps = MutexConfigGroup.from_path_lists(
            all_yamls(clack_xdg_dir / "global"),
            all_yamls(clack_apps_dir / "all"),
        )

        # app-specific user config files
        #
        # e.g. ~/.config/APP/APP.yml OR ~/.config/APP/config.yml OR
        #      ~/.config/clack/apps/APP.yml...
        user_group_for_this_app = MutexConfigGroup.from_path_lists(
            all_yamls(full_xdg_dir / app_name),
            all_yamls(full_xdg_dir / "config"),
            all_yamls(clack_apps_dir / app_name),
        )

        # app-specific config files that are local to the CWD
        #
        # e.g. ./APP.yml OR ./APP.yaml OR ./APP/APP.yml OR ./APP/config.yaml OR
        #      ./.APP/APP.yaml OR ./.APP/config.yml...
        local_group_for_this_app = MutexConfigGroup.from_path_lists(
            all_yamls(app_name),
            all_yamls(app_path / app_name),
            all_yamls(app_path / "config"),
            all_yamls(hidden_app_path / app_name),
            all_yamls(hidden_app_path / "config"),
        )

        ##### Populate and then return dict of configuration values...
        result: Dict[str, Any] = {}

        # Fill the `result` configuration mapping by calling the
        # MutexConfigGroup.populate_config_map() method for each group...
        #
        # WARNING: Order matters here since groups called first will
        # potentially have their configurations overwritten by groups called
        # later.
        user_group_for_all_apps.populate_config_map(result)
        user_group_for_this_app.populate_config_map(result)
        local_group_for_this_app.populate_config_map(result)

        return result

    return config_settings
