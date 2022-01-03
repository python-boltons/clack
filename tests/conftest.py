"""This file contains shared fixtures and pytest hooks.

https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""

import logging
from typing import Iterator

from freezegun import freeze_time
from pytest import fixture
import structlog

from clack import _dynvars as dyn


pytest_plugins = ["logrus.pytest_plugin"]


@fixture(autouse=True, scope="session")
def frozen_time() -> Iterator[None]:
    """Freeze time until our tests are done running."""
    with freeze_time("2021-09-06T15:45:03.585481Z"):
        yield


@fixture(autouse=True)
def clear_lru_cache() -> None:
    """Clear function LRU cache before each test.

    Clears cache of functions that have been decorated with
    @functools.lru_cache before each test.
    """

    dyn.get_app_name.cache_clear()
    dyn.get_config_defaults.cache_clear()


@fixture(autouse=True)
def clear_loggers() -> None:
    """Remove handlers from all loggers and unconfigure structlog.

    See https://github.com/pytest-dev/pytest/issues/5502 for an explanation on
    why we need this fixture.
    """
    loggers = [logging.getLogger()] + list(
        logging.Logger.manager.loggerDict.values()  # type: ignore[arg-type]
    )
    for logger in loggers:
        handlers = getattr(logger, "handlers", [])
        for handler in handlers:
            logger.removeHandler(handler)

    structlog.reset_defaults()
