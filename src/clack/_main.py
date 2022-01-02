"""Defines the clack.main_factory() function."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
import signal
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Protocol,
    Sequence,
    Union,
    get_type_hints,
    overload,
)

from logrus import Log, Logger, init_logging

from ._config import AbstractConfig, Config_T
from ._dynvars import clack_envvars_set


Parser = Callable[
    [Sequence[str]], Union[ArgumentParser, Namespace, Dict[str, Any]]
]
ParserFactory = Callable[[], ArgumentParser]
Runner = Callable[[Config_T], int]


class MainType(Protocol):
    """Type of the `main()` function returned by `main_factory()`."""

    def __call__(self, argv: Sequence[str] = None) -> int:
        """This method captures the `main()` function's signature."""


@overload
def main_factory(app_name: str, run: Runner) -> MainType:
    ...


@overload
def main_factory(
    app_name: str, *, runners: Iterable[Runner], parser: Parser
) -> MainType:
    ...


@overload
def main_factory(
    app_name: str, *, runners: Iterable[Runner], parser: ParserFactory
) -> MainType:
    ...


def main_factory(
    app_name: str,
    run: Runner = None,
    *,
    runners: Iterable[Runner] = None,
    parser: Parser | ParserFactory | None = None
) -> MainType:
    """Factory used to create a new `main()` function.

    Returns:
        A generic main() function to be used as a script's entry point.
    """

    del runners
    del parser

    def main_worker(run: Runner, cfg: AbstractConfig) -> int:
        verbose: int = getattr(cfg, "verbose", 0)
        logs: List[Log] = getattr(cfg, "logs", [])

        init_logging(logs=logs, verbose=verbose)

        logger = Logger("clack", app_name=app_name, cfg=cfg)

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

    def main(argv: Sequence[str] = None) -> int:
        if argv is None:  # pragma: no cover
            argv = sys.argv

        assert run is not None
        run_hints = get_type_hints(run)
        try:
            config_type = run_hints["cfg"]
        except KeyError as e:
            raise RuntimeError(
                "Logic Error! Every runner function should have a 'cfg' kwarg!"
            ) from e

        with clack_envvars_set(app_name, config_type):
            cfg = config_type.from_cli_args(argv)

        return main_worker(run, cfg)

    return main
