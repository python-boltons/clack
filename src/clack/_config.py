"""Contains the base configuration class for clack."""

from __future__ import annotations

from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from logrus import Log
from pydantic import BaseSettings
from typist import PathLike

from . import xdg
from ._config_file import YAMLConfigFile
from .types import ClackConfigFile, Config_T


_SettingsSource = Callable[[BaseSettings], Dict[str, Any]]


class Config(BaseSettings):
    """Default CLI arguments / app configuration."""

    config_file: Optional[ClackConfigFile] = None
    logs: List[Log] = []
    verbose: int = 0

    @classmethod
    def from_cli_args(cls: Type[Config_T], argv: Sequence[str]) -> Config_T:
        """Dummy function so this class follows ClackConfig protocol."""
        del argv
        raise NotImplementedError(
            "Basic clack applications (i.e. clack applications that do not use"
            " CLI subcommands) MUST define a from_cli_args() class method on"
            " their clack.Config subclass."
        )

    class Config:
        """Pydantic BaseSettings Configuration.

        NOTE:
            It is an unfortunate coincidence that this class must be named the
            same as its parent. This is a pydantic convention, but we (clack
            library maintainers) refuse to give up on the 'Config' naming
            scheme.
        """

        # Raise an Exception if anyone tries to modify the configuration
        # classes' attributes after it has been instantiated.
        allow_mutation = False

        # Allow extra init arguments to be passed into the configuration class
        # at initialization time (just ignore them).
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
            del file_secret_settings
            return (
                init_settings,
                env_settings,
                _config_settings_factory(YAMLConfigFile),
            )


def _config_settings_factory(
    config_file_type: Type[ClackConfigFile],
) -> _SettingsSource:
    """Configuration Settings Factory Function

    Factory function that returns a pydantic.BaseSettings source callable that
    reads values from one or more YAML config file.
    """

    class MutexConfigGroup:
        """Mutually Exclusive Configuration File Group.

        A single MutexConfigGroup object specifies one or more configuration
        file locations. We will ONLY load configuration values from the FIRST
        configuration file in this group that exists on disk (if any do).
        """

        def __init__(self, config_paths: List[Path], *, set_config_file: bool):
            self.config_paths = config_paths
            self.set_config_file = set_config_file

        @classmethod
        def from_path_lists(
            cls,
            *path_like_lists: Union[List[Path], List[str]],
            set_config_file: bool = True,
        ) -> "MutexConfigGroup":
            """MutexConfigGroup class constructor.

            Given N lists of config file paths, construct a new
            MutexConfigGroup object.
            """
            flat_path_list = []
            for path_like_list in path_like_lists:
                for path_like in path_like_list:
                    flat_path_list.append(Path(path_like))
            return cls(flat_path_list, set_config_file=set_config_file)

        def populate_config_map(
            self, mut_config_map: MutableMapping[str, Any]
        ) -> None:
            """Populate values for a config mapping using this mutex group.

            Set configuration options (by adding keys to the ``mut_config_map``
            mapping) using (at most) one of the config files corresponding with
            this MutexConfigGroup.
            """
            for config_path in self.config_paths:
                if config_path.is_file():
                    config_file = config_file_type(config_path)
                    config_dict = config_file.to_dict().unwrap()
                    mut_config_map.update(config_dict)

                    if self.set_config_file:
                        mut_config_map["config_file"] = config_file

                    break

    def all_extensions(name: PathLike) -> List[str]:
        """Helper function that adds support for all config filename exts."""
        name = str(name)
        return [name + "." + ext for ext in config_file_type.extensions]

    def config_settings(settings: BaseSettings) -> Dict[str, Any]:
        """The pydantic.BaseSettings source callable that we will return."""
        from . import _dynvars as dyn

        del settings

        app_name = dyn.get_app_name()
        config_file = dyn.get_config_file()

        if config_file is None:
            return config_settings_from_app_name(app_name)
        else:
            return config_settings_from_config_file(config_file)

    def config_settings_from_app_name(app_name: str) -> Dict[str, Any]:
        """Load settings from multiple configuration files based on `app_name`.

        NOTE:
            This function is only used when a user has NOT specified an
            explicit config file location (e.g. via --config=foo.yml).
        """
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
        # Note that we do NOT set the Config.config_file setting if the only
        # configuration file found is used by all apps (i.e. belongs to the
        # following MutexConfigGroup).
        #
        # e.g. ~/.config/clack/global.yml OR ~/.config/clack/apps/all.yml...
        user_group_for_all_apps = MutexConfigGroup.from_path_lists(
            all_extensions(clack_xdg_dir / "global"),
            all_extensions(clack_apps_dir / "all"),
            set_config_file=False,
        )

        # app-specific user config files
        #
        # e.g. ~/.config/APP/APP.yml OR ~/.config/APP/config.yml OR
        #      ~/.config/clack/apps/APP.yml...
        user_group_for_this_app = MutexConfigGroup.from_path_lists(
            all_extensions(full_xdg_dir / app_name),
            all_extensions(full_xdg_dir / "config"),
            all_extensions(clack_apps_dir / app_name),
        )

        # app-specific config files that are local to the CWD
        #
        # e.g. ./APP.yml OR ./APP.yaml OR ./APP/APP.yml OR ./APP/config.yaml OR
        #      ./.APP/APP.yaml OR ./.APP/config.yml...
        local_group_for_this_app = MutexConfigGroup.from_path_lists(
            all_extensions(app_name),
            all_extensions(app_path / app_name),
            all_extensions(app_path / "config"),
            all_extensions(hidden_app_path / app_name),
            all_extensions(hidden_app_path / "config"),
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

    def config_settings_from_config_file(config_file: Path) -> Dict[str, Any]:
        """Load settings from a single configuration file.

        NOTE:
            This function is only used when a user has specified an explicit
            config file location (e.g. via --config=foo.yml).
        """
        result: Dict[str, Any] = {}
        single_file_group = MutexConfigGroup.from_path_lists([config_file])
        single_file_group.populate_config_map(result)
        return result

    return config_settings
