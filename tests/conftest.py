"""This file contains shared fixtures and pytest hooks.

https://docs.pytest.org/en/6.2.x/fixture.html#conftest-py-sharing-fixtures-across-multiple-files
"""

import logging
from typing import Iterator, cast

from freezegun import freeze_time
from pytest import fixture
import structlog


pytest_plugins = ["clack.pytest_plugin", "logrus.pytest_plugin"]


@fixture(autouse=True, scope="session")
def frozen_time() -> Iterator[None]:
    """Freeze time until our tests are done running."""
    with freeze_time("2021-09-06T15:45:03.585481Z"):
        yield


@fixture(autouse=True)
def clear_loggers() -> None:
    """Remove handlers from all loggers and unconfigure structlog.

    See https://github.com/pytest-dev/pytest/issues/5502 for an explanation on
    why we need this fixture.
    """
    manager_loggers = cast(
        list[logging.Logger], list(logging.Logger.manager.loggerDict.values())
    )
    loggers = [logging.getLogger()] + list(manager_loggers)
    for logger in loggers:
        handlers = getattr(logger, "handlers", [])
        for handler in handlers:
            logger.removeHandler(handler)

    structlog.reset_defaults()
