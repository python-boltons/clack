"""E2E Test Application that uses Sub-commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Literal, Sequence

import clack
from clack.types import ClackRunner


# TEST | Basic test of 'bar' subcommand.
# --------------------------------------
# ARGS:     bar 5
# OUTPUT:   bar=5, barbar=BARBAR

# TEST | Slightly more complicated 'bar' test.
# --------------------------------------------
# ARGS:     bar --bar=foobar 5
# OUTPUT:   bar=5, barbar=foobar

# TEST | Basic test of 'baz' subcommand.
# --------------------------------------
# ARGS:     baz --baz
# OUTPUT:   baz=True

# TEST | Basic test of 'foo' subcommand.
# --------------------------------------
# ARGS:     foo --foo FOO
# OUTPUT:   foo=FOO foo_txt=foo.txt

# TEST | Do envvars work?
# -----------------------
# ARGS:     foo
# ENV:      FOO=KUNGFOO
# OUTPUT:   foo=KUNGFOO foo_txt=foo.txt

# TEST | Do envvars override defaults?
# ------------------------------------
# ARGS:     bar 5
# ENV:      BARBAR=foobar
# OUTPUT:   bar=5, barbar=foobar

# TEST | Does a config file work?
# -------------------------------
# ARGS:     foo
# CONFIG:   subcommands.yml {"foo": "FOOCONF"}
# OUTPUT:   foo=FOOCONF foo_txt=foo.txt

# TEST | Do envvars override config files?
# ----------------------------------------
# ARGS:     foo
# CONFIG:   subcommands.yml {"foo": "FOOCONF"}
# ENV:      FOO=FOOENV
# OUTPUT:   foo=FOOENV foo_txt=foo.txt

# TEST | Are unknown options ignored?
# -----------------------------------
# ARGS:     foo --foo FOO --ignored
# OUTPUT:   foo=FOO foo_txt=foo.txt


BarCommand = Literal["bar"]
BazCommand = Literal["baz"]
FooCommand = Literal["foo"]
Command = Literal[BarCommand, BazCommand, FooCommand]


# The ALL_RUNNERS list is populated later by the `register_runner` decorator.
ALL_RUNNERS: List[ClackRunner] = []
register_runner = clack.register_runner_factory(ALL_RUNNERS)


class Config(clack.Config):
    """Shared Configuration."""

    command: Command


class BarConfig(Config):
    """The 'bar' subcommand's configuration."""

    bar: int
    barbar: str = "BARBAR"
    command: BarCommand


class BazConfig(Config):
    """The 'baz' subcommand's configuration."""

    baz: bool
    command: BazCommand


class FooConfig(Config):
    """The 'foo' subcommand's configuration."""

    command: FooCommand
    foo: str
    foo_txt: Path = Path("foo.txt")


def clack_parser(argv: Sequence[str]) -> dict[str, Any]:
    """Parse CLI arguments."""
    parser = clack.Parser()
    new_command = clack.new_command_factory(parser)

    bar_parser = new_command("bar", help="The 'bar' subcommand.")
    bar_parser.add_argument("bar", type=int)
    bar_parser.add_argument("--bar", dest="barbar")

    baz_parser = new_command("baz", help="The 'baz' subcommand.")
    baz_parser.add_argument("--baz", action="store_true")

    foo_parser = new_command("foo", help="The 'foo' subcommand.")
    foo_parser.add_argument("--foo")
    foo_parser.add_argument("--foo-txt", dest="foo_txt", type=Path)
    foo_parser.add_argument("--ignored", action="store_true")

    args = parser.parse_args(argv[1:])

    return vars(args)


@register_runner
def run_bar(cfg: BarConfig) -> int:
    """Runner function."""
    print(f"bar={cfg.bar}, barbar={cfg.barbar}")
    return 0


@register_runner
def run_baz(cfg: BazConfig) -> int:
    """Runner function."""
    print(f"baz={cfg.baz}")
    return 0


@register_runner
def run_foo(cfg: FooConfig) -> int:
    """Runner function."""
    print(f"foo={cfg.foo} foo_txt={cfg.foo_txt}")
    return 0


main = clack.main_factory(
    "subcommands", runners=ALL_RUNNERS, parser=clack_parser
)
