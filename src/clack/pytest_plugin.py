"""A pytest plugin for testing the clack package.

This plugin can be enabled via the `pytest_plugins` conftest.py variable. This
allows us to use this plugin in external packages' tests instead of just for
this package's tests.

Examples:
    The following line should be found in the "tests/conftest.py" file:

    >>> pytest_plugins = ["clack.pytest_plugin"]
"""

from pathlib import Path
from typing import Any, Protocol, Type

from _pytest.fixtures import SubRequest
from pytest import fixture

from ._config_file import YAMLConfigFile
from .types import ClackConfigFile


class MakeConfigFile(Protocol):
    """Type of the function returned by `make_config_file()`."""

    def __call__(self, basename: str, **kwargs: Any) -> ClackConfigFile:
        """Captures the `make_config_file()` function's signature."""


@fixture(name="make_config_file", params=[YAMLConfigFile])
def make_config_file_fixture(
    request: SubRequest, tmp_path: Path
) -> MakeConfigFile:
    """Returns a function that can be used to generate ClackConfigFile objects.

    The associated config file is first instantiated using the 'kwargs'
    provided by the caller.
    """

    def make_config_file(basename: str, **kwargs: Any) -> ClackConfigFile:
        path = tmp_path / basename
        path.parent.mkdir(parents=True, exist_ok=True)

        config_file_type: Type[ClackConfigFile] = request.param
        return config_file_type.new(path, **kwargs)

    return make_config_file
