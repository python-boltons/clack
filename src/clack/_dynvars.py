"""Contains utilities to set and retrieve dynamic variable values.

This module is a bit of a HACK, but is better than using mutable global
variables IMO.
"""

from __future__ import annotations

import codecs
from contextlib import contextmanager
import os
from pathlib import Path
import pickle
from typing import Any, Final, Iterable, Iterator, Optional, Type

from ._config import AbstractConfig


_CODECS_ENCODING: Final = "base64"
_NO_CONFIG_FILE: Final = "DEFAULT_CLACK_CONFIG_FILE_LIST"


@contextmanager
def clack_envvars_set(
    app_name: str,
    config_types: Iterable[Type[AbstractConfig]],
    *,
    config_file: Path = None,
) -> Iterator[None]:
    """Context manager that sets temporary envvars.

    The following envvars are set on __enter__ and removed on __exit__:
        - CLACK_APP_NAME
        - CLACK_CONFIG_DEFAULTS
        - CLACK_CONFIG_FILE
    """
    config_defaults = {}
    for some_config_type in config_types:
        some_config_defaults = _config_defaults_from_config_type(
            some_config_type
        )
        config_defaults.update(some_config_defaults)

    os.environ["CLACK_APP_NAME"] = app_name
    os.environ["CLACK_CONFIG_DEFAULTS"] = codecs.encode(
        pickle.dumps(config_defaults), _CODECS_ENCODING
    ).decode()
    os.environ["CLACK_CONFIG_FILE"] = (
        _NO_CONFIG_FILE if config_file is None else str(config_file)
    )

    yield

    del os.environ["CLACK_APP_NAME"]
    del os.environ["CLACK_CONFIG_DEFAULTS"]
    del os.environ["CLACK_CONFIG_FILE"]


def _config_defaults_from_config_type(
    config_type: Type[AbstractConfig],
) -> dict[str, Any]:
    result = {}
    for key, value in config_type.__fields__.items():
        if value.default is not None or value.allow_none:
            result[key] = value.default
    return result


def get_app_name() -> str:
    """Getter function for CLACK_APP_NAME envvar.

    Raises:
        A RuntimeError if the CLACK_APP_NAME envvar is not defined.
    """
    with _catch_key_error("get_app_name"):
        return os.environ["CLACK_APP_NAME"]


def get_config_defaults() -> dict[str, Any]:
    """Getter function for CLACK_CONFIG_DEFAULTS envvar.

    Raises:
        A RuntimeError if the CLACK_CONFIG_DEFAULTS envvar is not defined.
    """
    with _catch_key_error("get_config_defaults"):
        config_defaults_string = os.environ["CLACK_CONFIG_DEFAULTS"]

    result: dict[str, Any] = pickle.loads(
        codecs.decode(config_defaults_string.encode(), _CODECS_ENCODING)
    )
    return result


def get_config_file() -> Optional[Path]:
    """Getter function for CLACK_CONFIG_FILE envvar.

    Raises:
        A RuntimeError if the CLACK_CONFIG_FILE envvar is not defined.
    """
    with _catch_key_error("get_config_file"):
        config_file = os.environ["CLACK_CONFIG_FILE"]

    if config_file == _NO_CONFIG_FILE:
        return None
    else:
        return Path(config_file)


@contextmanager
def _catch_key_error(func_name: str) -> Iterator[None]:
    try:
        yield
    except KeyError as e:
        raise RuntimeError(
            f"The {func_name}() function MUST be called INSIDE the context"
            " that clack_envvars_set() creates."
        ) from e
