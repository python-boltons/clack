"""E2E test application."""

from __future__ import annotations

from typing import Sequence

import clack


### TEST CASE 1
#
# ARGS:     --foo=KUNG -B2
# OUTPUT:   foo=KUNG bar=2 baz=False
#
### END TEST CASE

### TEST CASE 2
#
# ARGS:     --some-bar=3 --baz
# OUTPUT:   foo=FOO bar=3 baz=True
#
### END TEST CASE

### TEST CASE 3
#
# ARGS:     --baz
# ENV:      BAR=4
# OUTPUT:   foo=FOO bar=4 baz=True
#
### END TEST CASE

### TEST CASE 4
#
# ARGS:     -B1 --baz
# ENV:      BAR=4 FOO=foofoo
# OUTPUT:   foo=foofoo bar=1 baz=True
#
### END TEST CASE


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
        kwargs = clack.args_to_kwargs(args)

        return Config(**kwargs)


def run(cfg: Config) -> int:
    """Runner function."""
    print(f"foo={cfg.foo} bar={cfg.bar} baz={cfg.baz}")
    return 0


main = clack.main_factory("app", run, Config)
if __name__ == "__main__":
    main()
