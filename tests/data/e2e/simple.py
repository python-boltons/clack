"""E2E test application."""

from __future__ import annotations

from typing import Sequence

import clack


# TEST CASE | Basic CLI opts and config class attribute defaults work.
# ----------+---------------------------------------------------------
# ARGS:     --foo=KUNG -B2
# OUTPUT:   foo=KUNG bar=2 baz=False

# TEST CASE | The 'dest' kwarg works.
# ----------+------------------------
# ARGS:     --some-bar=3 --baz
# OUTPUT:   foo=FOO bar=3 baz=True

# TEST CASE | Environment variables work.
# ----------+----------------------------
# ARGS:     --baz
# ENV:      BAR=4
# OUTPUT:   foo=FOO bar=4 baz=True

# TEST CASE | CLI options override envvars.
# ----------+------------------------------
# ARGS:     -B1 --baz
# ENV:      BAR=4 FOO=foofoo
# OUTPUT:   foo=foofoo bar=1 baz=True

# TEST CASE | Configuration files work.
# ----------+--------------------------
# ARGS:     --baz
# CONFIG:   simple.yml {"foo": "FOOFOOFOO", "bar": "456"}
# OUTPUT:   foo=FOOFOOFOO bar=456 baz=True

# TEST CASE | Config files are overriden by envvars and CLI opts.
# ----------+----------------------------------------------------
# ARGS:     --baz
# CONFIG:   simple/simple.yaml {"foo": "FOOFOOFOO", "bar": "456", "baz": false}
# ENV:      BAR=123
# OUTPUT:   foo=FOOFOOFOO bar=123 baz=True

# TEST CASE | XDG locations should be checked.
# ----------+---------------------------------
# ARGS:     --baz
# CONFIG:   simple/config.yml {"bar": "456"}
# CONFIG:   XDG/simple.yml {"foo": "UserFoo"}
# OUTPUT:   foo=UserFoo bar=456 baz=True

# TEST CASE | XDG locations should be overriden by user locations.
# ----------+-----------------------------------------------------
# ARGS:     --baz
# CONFIG:   .simple/config.yml {"foo": "LocalFoo"}
# CONFIG:   XDG/simple.yml {"foo": "UserFoo", "bar": "456"}
# OUTPUT:   foo=LocalFoo bar=456 baz=True


class Config(clack.Config):
    """Application Config."""

    foo: str = "FOO"
    bar: int
    baz: bool = False

    @classmethod
    def from_cli_args(cls, argv: Sequence[str]) -> Config:
        """Parse CLI arguments."""
        parser = clack.Parser()
        parser.add_argument("-f", "--foo")
        parser.add_argument("-B", "--some-bar", dest="bar", type=int)
        parser.add_argument("--baz", action="store_true")

        args = parser.parse_args(argv[1:])
        kwargs = clack.filter_cli_args(args)

        return Config(**kwargs)


def run(cfg: Config) -> int:
    """Runner function."""
    print(f"foo={cfg.foo} bar={cfg.bar} baz={cfg.baz}")
    return 0


main = clack.main_factory("simple", run)
