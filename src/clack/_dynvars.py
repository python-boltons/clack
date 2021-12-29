"""Contains utilities to set and retrieve dynamic variable values.

This module is a bit of a HACK, but is better than using mutable global
variables IMO.
"""

from contextlib import contextmanager
from functools import lru_cache
import os
from typing import Iterator


@contextmanager
def clack_envvars_set(app_name: str) -> Iterator[None]:
    """Context manager that sets temporary envvars.

    The following envvars are set on __enter__ and removed on __exit__:
        - CLACK_APP_NAME
    """
    os.environ["CLACK_APP_NAME"] = app_name
    yield
    del os.environ["CLACK_APP_NAME"]


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
