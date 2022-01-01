"""Contains utilities to set and retrieve dynamic variable values.

This module is a bit of a HACK, but is better than using mutable global
variables IMO.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import json
import os
from typing import Any, Iterator, Type

from ._config import AbstractConfig


@contextmanager
def clack_envvars_set(
    app_name: str, config_type: Type[AbstractConfig]
) -> Iterator[None]:
    """Context manager that sets temporary envvars.

    The following envvars are set on __enter__ and removed on __exit__:
        - CLACK_APP_NAME
        - CLACK_CONFIG_DEFAULTS
    """
    config_defaults = _config_defaults_from_config_type(config_type)
    os.environ["CLACK_APP_NAME"] = app_name
    os.environ["CLACK_CONFIG_DEFAULTS"] = json.dumps(config_defaults)

    yield

    del os.environ["CLACK_APP_NAME"]
    del os.environ["CLACK_CONFIG_DEFAULTS"]


def _config_defaults_from_config_type(
    config_type: Type[AbstractConfig],
) -> dict[str, Any]:
    result = {}
    for key, value in config_type.__fields__.items():
        if value.default is not None or value.allow_none:
            result[key] = value.default
    return result


@lru_cache
def get_app_name() -> str:
    """Getter function for CLACK_APP_NAME envvar.

    Raises:
        A RuntimeError if the CLACK_APP_NAME envvar is not defined.
    """
    try:
        return os.environ["CLACK_APP_NAME"]
    except KeyError as e:
        raise RuntimeError(
            "The get_app_name() function MUST be called INSIDE the context"
            " that clack_envvars_set() creates."
        ) from e


@lru_cache
def get_config_defaults() -> dict[str, Any]:
    """Getter function for CLACK_CONFIG_DEFAULTS envvar.

    Raises:
        A RuntimeError if the CLACK_CONFIG_DEFAULTS envvar is not defined.
    """
    try:
        config_defaults_string = os.environ["CLACK_CONFIG_DEFAULTS"]
    except KeyError as e:
        raise RuntimeError(
            "The get_config_defaults() function MUST be called INSIDE the"
            " context that clack_envvars_set() creates."
        ) from e
    else:
        result: dict[str, Any] = json.loads(config_defaults_string)
        return result
