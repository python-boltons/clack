"""A pytest plugin for testing the logrus package.

This plugin can be enabled via the `pytest_plugins` conftest.py variable. This
allows us to use this plugin in external packages' tests instead of just for
this package's tests.

Examples:
    The following line should be found in the "tests/conftest.py" file:

    >>> pytest_plugins = ["clack.pytest_plugin"]
"""

from pathlib import Path
from typing import Any, Protocol

from pytest import fixture
import yaml

from ._config_file import ConfigFile, YAMLConfigFile


class MakeConfigFile(Protocol):
    """Type of the function returned by `make_config_file()`."""

    def __call__(self, basename: str, **kwargs: Any) -> ConfigFile:
        """Captures the `make_config_file()` function's signature."""


@fixture(name="make_config_file")
def make_config_file_fixture(tmp_path: Path) -> MakeConfigFile:
    """Returns a function that can be used to generate ConfigFile objects.

    The associated config file is first instantiated using the 'kwargs'
    provided by the caller.
    """

    def make_config_file(basename: str, **kwargs: Any) -> ConfigFile:
        config_dict = dict(**kwargs)

        path = tmp_path / basename
        path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize config file...
        with path.open("w+") as f:
            yaml.dump(config_dict, f, allow_unicode=True)

        return YAMLConfigFile(path)

    return make_config_file
