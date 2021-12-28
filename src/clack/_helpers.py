"""Defines miscellaneous helper functions."""

from __future__ import annotations

import argparse
from typing import Any, List, Protocol


class NewCommand(Protocol):
    """Type of the function returned by `new_command_factory()`."""

    def __call__(
        self,
        name: str,
        *,
        help: str,  # pylint: disable=redefined-builtin
        **kwargs: Any,
    ) -> argparse.ArgumentParser:
        """This method captures the `new_command()` function's signature."""


def new_command_factory(
    parser: argparse.ArgumentParser,
    *,
    dest: str = "command",
    required: bool = True,
    description: str = None,
    **kwargs: Any,
) -> NewCommand:
    """Returns a `new_command()` function that can be used to add subcommands.

    Args:
        parser: The argparse parser that we want to add subcommands to.
        dest: The attribute name that the subcommand name will be stored under
          inside the Namespace object.
        required: Will this subcommand be required or optional?
        description: This argument describes what the subcommand is used for.
        kwargs: These keyword arguments are relayed to the
          ``parser.add_subparsers()`` function call.
    """
    subparsers = parser.add_subparsers(
        dest=dest, required=required, description=description, **kwargs
    )

    def new_command(
        name: str,
        *,
        help: str,  # pylint: disable=redefined-builtin
        **inner_kwargs: Any,
    ) -> argparse.ArgumentParser:
        return subparsers.add_parser(
            name,
            formatter_class=parser.formatter_class,
            help=help,
            description=help,
            **inner_kwargs,
        )

    return new_command


class comma_list_or_file:
    """Namespace class for comma list CLI arguments.

    These CLI arguments can either be a comma-separated list or a new-line
    separated file.
    """

    @staticmethod
    def parse(arg: str) -> List[str]:
        """
        Used to interpret a CLI argument that is allowed to be either a
        comma-separated list or a file containing values separated by newlines.

        Args:
            arg: This argument should be one of the following: [i] A
              comma-separated list of values. [ii] A filename corresponding to
              a file containing a list of newline-separated values.

        Returns:
            The list of corresponding option values.
        """
        try:
            results = []
            for line in open(arg, "r"):
                line = line.rstrip("\n")
                if not line or " " in line:
                    raise RuntimeError(
                        "This file doesn't look like it contains option"
                        " values. Maybe this file was intended to be a"
                        " single-value, comma-separated list (i.e. no commas)?"
                    )

                results.append(line)

            return results
        except (IOError, RuntimeError):
            return arg.split(",")

    @staticmethod
    def help(msg: str) -> str:
        """
        Updates the help message of an argparse argument which accepts either a
        comma-separated list or a file containing values separated by newlines.
        """
        COMMA_LIST_OR_FILE_DESC = (
            "This option can accept either a comma-separated list or a file"
            " which contains a list of values (separated by newlines)."
        )

        new_msg = msg
        if not new_msg.endswith(" "):
            new_msg += " "

        return new_msg + COMMA_LIST_OR_FILE_DESC