"""Defines the clack.main_factory() function."""

from __future__ import annotations

from pathlib import Path
import signal
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    Iterable,
    List,
    Optional,
    Protocol,
    Sequence,
    Type,
    cast,
    get_type_hints,
    overload,
)

from logrus import Log, Logger, init_logging
from typist import literal_to_list

from . import _dynvars as dyn
from ._config import AbstractConfig, Config_T
from ._parser import filter_cli_args


Parser = Callable[[Sequence[str]], Dict[str, Any]]
Runner = Callable[[Config_T], int]

ASSERT_MAIN_FACTORY_PRECOND: Final = (
    "EXACTLY ONE of the following MUST be true when calling the"
    " clack.main_factory() function: (1) The 'run' positional argument is"
    " provided OR (2) the 'runners' and 'parser' keyword-only arguments are"
    " BOTH provided."
)
ASSERT_MAIN_RUNNERS_PRECOND: Final = (
    "ALL runners must have a clack.Config 'cfg' positional argument which"
    ' inherit from the SAME shared clack.Config subclass. This "shared'
    " Config\" should have a 'command' attribute that is typed as a"
    " typing.Literal, say CommandLiteral. Additionally, all subclasses of this"
    " shared Config MUST have a 'command' attribute that is typed as a"
    " typing.Literal which is a a subtype of CommandLiteral"
)


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


def main_factory(
    app_name: str,
    run: Runner = None,
    *,
    runners: Iterable[Runner] = None,
    parser: Parser = None,
) -> MainType:
    """Factory used to create a new `main()` function.

    Returns:
        A generic main() function to be used as a script's entry point.
    """

    run_is_set = bool(run is not None)
    kwargs_only = bool(runners is not None and parser is not None)

    assert run_is_set or kwargs_only, ASSERT_MAIN_FACTORY_PRECOND
    assert not (run_is_set and kwargs_only), ASSERT_MAIN_FACTORY_PRECOND

    def main_run(argv: Sequence[str]) -> int:
        assert run is not None

        config_file = _get_config_file(argv)
        config_type = _get_run_cfg(run)
        with dyn.clack_envvars_set(
            app_name, [config_type], config_file=config_file
        ):
            cfg = config_type.from_cli_args(argv)

        return do_main_work(run, cfg)

    def main_runners(argv: Sequence[str]) -> int:
        assert runners is not None
        assert parser is not None

        runner_list = list(runners)
        all_config_types = _get_all_config_types(runner_list)

        config_file = _get_config_file(argv)
        with dyn.clack_envvars_set(
            app_name, all_config_types, config_file=config_file
        ):
            parser_kwargs = parser(argv)

            config_type = _config_type_from_command(
                all_config_types, parser_kwargs["command"]
            )

            filtered_kwargs = filter_cli_args(parser_kwargs)
            cfg = config_type(**filtered_kwargs)

        run = _main_runner_factory(runners)
        return do_main_work(run, cfg)

    def do_main_work(runner: Runner, cfg: AbstractConfig) -> int:
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
            status = runner(cfg)
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

    def wrap_main(outer_main: Callable[[Sequence[str]], int]) -> MainType:
        def inner_main(argv: Sequence[str] = None) -> int:
            if argv is None:  # pragma: no cover
                argv = sys.argv

            return outer_main(argv)

        return inner_main

    if run is None:
        return wrap_main(main_runners)
    else:
        return wrap_main(main_run)


def _get_config_file(argv: Sequence[str]) -> Optional[Path]:
    for opt in ["-c", "--config"]:
        if opt in argv:
            idx = argv.index(opt)
            return Path(argv[idx + 1])

        for argv_opt in argv:
            if opt in argv_opt:
                cfg_fname = argv_opt.replace(opt, "").lstrip("=")
                return Path(cfg_fname)

    return None


def _main_runner_factory(runners: Iterable[Runner]) -> Runner:
    def run(cfg: Any) -> int:
        for run in runners:
            run_config_type = _get_run_cfg(run)
            if isinstance(cfg, run_config_type):
                return run(cfg)

        return -1

    return run


def _get_run_cfg(run: Runner) -> Type[AbstractConfig]:
    run_hints = get_type_hints(run)
    try:
        cfg: Type[AbstractConfig] = run_hints["cfg"]
        return cfg
    except KeyError as e:
        raise AssertionError(
            "Logic Error! Every runner function should have a 'cfg' kwarg!"
        ) from e


def _config_type_from_command(
    all_config_types: Iterable[Type[AbstractConfig]],
    choosen_command: str,
) -> Type[AbstractConfig]:
    config_type_to_command = {}
    for some_config_type in all_config_types:
        some_command = _get_single_command(some_config_type)
        config_type_to_command[some_config_type] = some_command
        if some_command == choosen_command:
            return some_config_type

    raise AssertionError(
        "Logic Error! None of the given Config types seem to match the choosen"
        " sub-command.  |  "
        + ASSERT_MAIN_RUNNERS_PRECOND
        + f"  |  {config_type_to_command!r}"
    )


def _get_all_commands(config_type: Type[AbstractConfig]) -> List[str]:
    config_type_hints = get_type_hints(config_type)
    try:
        command_type = config_type_hints["command"]
    except KeyError as e:
        raise AssertionError(
            "Logic Error! When using sub-commands in your CLI interface with"
            " clack, ALL Config classes MUST have a 'command' attribute!"
        ) from e
    else:
        result = cast(List[str], literal_to_list(command_type))
        return result


def _get_single_command(config_type: Type[AbstractConfig]) -> str:
    all_commands = _get_all_commands(config_type)
    assert len(all_commands) == 1, (
        ASSERT_MAIN_RUNNERS_PRECOND + f" | {all_commands!r}"
    )
    return all_commands[0]


def _get_all_config_types(
    runners: Iterable[Runner],
) -> List[Type[AbstractConfig]]:
    result: List[Type[AbstractConfig]] = []
    for runner in runners:
        config_type = _get_run_cfg(runner)
        result.append(config_type)
    return result
