"""Tests for the clack package."""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, List, Literal, Sequence, Union

from _pytest.capture import CaptureFixture, CaptureResult
import logrus
import pytest
from pytest import fixture, mark, param
from pytest_mock.plugin import MockerFixture
import structlog
from syrupy.assertion import SnapshotAssertion as Snapshot

import clack


params = mark.parametrize
LoggerType = Literal["logging", "structlog"]


class Config(clack.Config):
    """Test Config for clack.main_factory()."""

    do_stuff: bool

    @classmethod
    def from_cli_args(cls, argv: Sequence[str]) -> "Config":
        """Constructs a new Config object from command-line arguments."""
        parser = clack.Parser()
        parser.add_argument("--do-stuff", action="store_true")

        args = parser.parse_args(argv[1:])
        kwargs = vars(args)

        return Config(**kwargs)


def run_factory(logger_type: LoggerType) -> Callable[[Any], int]:
    """This runner function is meant to be passed into clack.main_factory()."""
    log: Union[logging.Logger, logrus.BetterBoundLogger]
    if logger_type == "structlog":
        log = logrus.Logger("test")
    else:
        assert logger_type == "logging"
        log = logging.getLogger("test")

    def run(cfg: Config) -> int:
        print("Starting CLI test...")

        if logger_type == "structlog":
            log.trace(  # type: ignore[union-attr]
                "This is a %s level message.", "TRACE", log_level="TRACE"
            )

        log.debug("Can anyone hear me???")
        log.info("Are we going to do stuff?")
        log.warning("What stuff?!?!?!")

        if cfg.do_stuff:
            if logger_type == "structlog":
                log.info("Doing some %s...", "stuff", stuff="???")
            else:
                assert logger_type == "logging"
                log.info("Doing some %s...", "stuff")

        log.error("Did we do the stuff?!?!?!")
        return 0

    return run


def pformat_captured(captured: CaptureResult) -> str:
    """Pretty format a capsys captured object."""
    return (
        f"----- STDOUT -----\n{captured.out}\n\n----- STDERR"
        f" -----\n{captured.err}"
    )


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


@params("logger_type", ["logging", "structlog"])
@params(
    "args",
    (
        param([], id="no args (default: colored logging to stderr)"),
        param(["--do-stuff", "--log", "stderr@nocolor"], id="do stuff"),
        param(["--log", "null"], id="no logging"),
        param(["-v", "--log", "stderr@nocolor"], id="verbose to stderr"),
        param(["-v", "--log", "stdout@nocolor"], id="verbose to stdout"),
        param(["-vv", "--log", "stderr@nocolor"], id="very verbose to stderr"),
        param(["-vv", "--log", "stdout@nocolor"], id="very verbose to stdout"),
        param(
            ["-vvv", "--log", "stderr@nocolor"], id="super verbose to stderr"
        ),
        param(
            ["-vvv", "--log", "stdout@nocolor"], id="super verbose to stdout"
        ),
        param(["--log", "stdout@nocolor"], id="log to stdout"),
        param(["--log", "stdout:ERROR@nocolor"], id="log ERROR to stdout"),
        param(
            [
                "--log",
                "stderr@nocolor",
                "--log",
                "stdout@nocolor",
                "--do-stuff",
            ],
            id="log to stdout and stderr",
        ),
    ),
)
def test_log(
    mock_dynamic_log_fields: None,
    capsys: CaptureFixture,
    snapshot: Snapshot,
    args: List[str],
    logger_type: LoggerType,
) -> None:
    """Test the --log option.

    Tests the --log option using the main() function produced by
    clack.main_factory().
    """
    del mock_dynamic_log_fields

    run = run_factory(logger_type)
    main = clack.main_factory(run, Config)
    exit_code = main([""] + args)
    assert exit_code == 0

    captured = capsys.readouterr()

    pretty_captured = pformat_captured(captured)
    pretty_captured = re.sub("_Pydantic_([^_]+)_[^(]+", r"\1", pretty_captured)

    assert pretty_captured == snapshot


def test_help(mocker: MockerFixture) -> None:
    """Test the --help option."""
    # So we can capture --help output.
    mocker.patch("sys.exit")

    run = run_factory("structlog")
    main = clack.main_factory(run, Config)
    exit_code = main(["", "--help"])
    assert exit_code == 0


def test_new_command_factory() -> None:
    """Test the clack.new_command_factory() function."""
    parser = clack.Parser()

    new_command = clack.new_command_factory(parser, dest="command")

    foo = new_command("foo", help="Test FOO subcommand.")
    foo.add_argument("--bar", action="store_true", help="Test BAR option.")

    args = parser.parse_args(["foo", "--bar"])
    assert args.command == "foo"
    assert args.bar


def test_config_is_immutable() -> None:
    """Test that the Config object's attributes are immutable."""
    cfg = Config.from_cli_args(["", "--do-stuff"])
    assert cfg.do_stuff

    with pytest.raises(TypeError):
        cfg.do_stuff = False
