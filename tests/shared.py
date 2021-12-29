"""Functions / classes that are shared by multiple test files."""

from typing import Sequence

import clack


class Config(clack.Config):
    """Test Config for clack.main_factory()."""

    do_stuff: bool = False

    @classmethod
    def from_cli_args(cls, argv: Sequence[str]) -> "Config":
        """Constructs a new Config object from command-line arguments."""
        parser = clack.Parser()
        parser.add_argument("--do-stuff", action="store_true")

        args = parser.parse_args(argv[1:])
        kwargs = clack.args_to_kwargs(args)

        return Config(**kwargs)
