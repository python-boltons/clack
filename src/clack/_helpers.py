"""Defines miscellaneous helper functions."""

from __future__ import annotations

import argparse
from typing import Any, Callable, List, Mapping, MutableSequence

from ._parser import monkey_patch_parser
from .types import ClackNewCommand, ClackRunner


def new_command_factory(
    parser: argparse.ArgumentParser,
    *,
    dest: str = "command",
    required: bool = True,
    description: str = None,
    **kwargs: Any,
) -> ClackNewCommand:
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
        result: argparse.ArgumentParser = subparsers.add_parser(
            name,
            formatter_class=parser.formatter_class,
            help=help,
            description=help,
            **inner_kwargs,
        )
        monkey_patch_parser(result)
        return result

    return new_command


def register_runner_factory(
    mut_runner_registry: MutableSequence[ClackRunner],
) -> Callable[[ClackRunner], ClackRunner]:
    """Creates a decorator that can be used to register runner functions."""

    def register_runner(runner: ClackRunner) -> ClackRunner:
        mut_runner_registry.append(runner)
        return runner

    return register_runner


def filter_cli_args(
    args: argparse.Namespace | Mapping[str, Any],
) -> dict[str, Any]:
    """Filters args produced by 'parser' passed into clack.main_factory().

    Used to filter out argparse arguments which were NOT specified on the
    command-line.
    """
    from . import _dynvars as dyn
    from ._parser import ARGPARSE_ARGUMENT_DEFAULT

    if not isinstance(args, argparse.Namespace):
        kwargs = args
    else:
        kwargs = vars(args)

    config_defaults = dyn.get_config_defaults()

    result = {}
    for key, value in kwargs.items():
        if key in config_defaults and config_defaults[key] == value:
            continue

        if value is ARGPARSE_ARGUMENT_DEFAULT:
            continue

        result[key] = value
    return result


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
