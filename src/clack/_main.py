"""Defines the clack.main_factory() function."""

from __future__ import annotations

import signal
import sys
from typing import Callable, List, Protocol, Sequence, Type

from logrus import Log, Logger, init_logging

from ._config import Config_T
from ._dynvars import clack_envvars_set


class MainType(Protocol):
    """Type of the `main()` function returned by `main_factory()`."""

    def __call__(self, argv: Sequence[str] = None) -> int:
        """This method captures the `main()` function's signature."""


# @overload
# def main_factory(
#     app_name: str, run: Callable[[AbstractConfig], int]
# ) -> MainType:
#     ...


# @overload
# def main_factory(
#     app_name: str,
#     *,
#     runners: Iterable[Callable[[AbstractConfig], int]],
#     parser: Callable[[Sequence[str]], AbstractConfig]
# ) -> MainType:
#     ...


def main_factory(
    app_name: str, run: Callable[[Config_T], int], config_type: Type[Config_T]
) -> MainType:
    """Factory used to create a new `main()` function.

    Args:
        app_name: The name of the currently running application.
        run: A function that acts as the real entry point for a program.
        config_type: A pydantic.BaseSettings type that represents our
          application's config.

    Returns:
        A generic main() function to be used as a script's entry point.
    """

    def main(argv: Sequence[str] = None) -> int:
        if argv is None:  # pragma: no cover
            argv = sys.argv

        with clack_envvars_set(app_name, config_type):
            cfg = config_type.from_cli_args(argv)

        verbose: int = getattr(cfg, "verbose", 0)
        logs: List[Log] = getattr(cfg, "logs", [])

        init_logging(logs=logs, verbose=verbose)

        logger = Logger("clack", app_name=app_name, cfg=cfg).bind_fargs(
            argv=argv
        )

        # The following log messages will obviously only be visible if the
        # corresponding log level really is enabled, but stating the obvious in
        # this case seemed like the right thing to do so ¯\_(ツ)_/¯.
        logger.trace("TRACE level logging enabled.")
        logger.debug("DEBUG level logging enabled.")

        try:
            status = run(cfg)
        except KeyboardInterrupt:  # pragma: no cover
            logger.info("Received SIGINT signal. Terminating script...")
            return 128 + signal.SIGINT.value
        except Exception:  # pragma: no cover
            logger.exception(
                "An unrecoverable error has been raised. Terminating script..."
            )
            return 1
        else:
            return status

    return main
