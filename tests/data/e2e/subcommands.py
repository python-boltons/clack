"""E2E Test Application that uses Sub-commands."""

from __future__ import annotations

from typing import Any, Literal, Sequence

import clack


# TEST CASE | Basic test of 'bar' subcommand.
# ----------+--------------------------------
# ARGS:     bar 5
# OUTPUT:   bar=5

# TEST CASE | Basic test of 'baz' subcommand.
# ----------+--------------------------------
# ARGS:     baz --baz
# OUTPUT:   baz=True

# TEST CASE | Basic test of 'foo' subcommand.
# ----------+--------------------------------
# ARGS:     foo --foo FOO
# OUTPUT:   foo=FOO

# TEST CASE | Do envvars work?
# ----------+--------------------------------
# ARGS:     foo
# ENV:      FOO=KUNGFOO
# OUTPUT:   foo=KUNGFOO

# TEST CASE | Does a config file work?
# ----------+--------------------------------
# ARGS:     foo
# CONFIG:   subcommands.yml {"foo": "FOOCONF"}
# OUTPUT:   foo=FOOCONF


BarCommand = Literal["bar"]
BazCommand = Literal["baz"]
FooCommand = Literal["foo"]
Command = Literal[BarCommand, BazCommand, FooCommand]


class Config(clack.Config):
    """Shared Configuration."""

    command: Command


class BarConfig(Config):
    """The 'bar' subcommand's configuration."""

    bar: int
    command: BarCommand


class BazConfig(Config):
    """The 'baz' subcommand's configuration."""

    baz: bool
    command: BazCommand


class FooConfig(Config):
    """The 'foo' subcommand's configuration."""

    command: FooCommand
    foo: str


def clack_parser(argv: Sequence[str]) -> dict[str, Any]:
    """Parse CLI arguments."""
    parser = clack.Parser()
    new_command = clack.new_command_factory(parser)

    bar_parser = new_command("bar", help="The 'bar' subcommand.")
    bar_parser.add_argument("bar", type=int)

    baz_parser = new_command("baz", help="The 'baz' subcommand.")
    baz_parser.add_argument("--baz", action="store_true")

    foo_parser = new_command("foo", help="The 'foo' subcommand.")
    foo_parser.add_argument("--foo")

    args = parser.parse_args(argv[1:])

    return vars(args)


def run_bar(cfg: BarConfig) -> int:
    """Runner function."""
    print(f"bar={cfg.bar}")
    return 0


def run_baz(cfg: BazConfig) -> int:
    """Runner function."""
    print(f"baz={cfg.baz}")
    return 0


def run_foo(cfg: FooConfig) -> int:
    """Runner function."""
    print(f"foo={cfg.foo}")
    return 0


main = clack.main_factory(
    "subcommands", runners=[run_bar, run_baz, run_foo], parser=clack_parser
)