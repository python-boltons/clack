"""Defines the clack.Parser() helper function."""

from __future__ import annotations

import argparse
import importlib.metadata
from importlib.metadata import PackageNotFoundError, version as get_version
import inspect
import os
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    cast,
)

from logrus import Log, LogFormat, LogLevel, get_default_logfile
from typist import literal_to_list

from . import _dynvars as dyn
from ._config_file import YAMLConfigFile


ARGPARSE_ARGUMENT_DEFAULT = object()


def Parser(*args: Any, **kwargs: Any) -> argparse.ArgumentParser:
    """Wrapper for argparse.ArgumentParser."""

    app_name = dyn.get_app_name()

    stack = list(inspect.stack())
    stack.pop(0)
    frame = stack.pop(0).frame

    if kwargs.get("description") is None:
        try:
            kwargs["description"] = frame.f_globals["__doc__"]
        except KeyError:
            pass

    if kwargs.get("formatter_class") is None:
        kwargs["formatter_class"] = _HelpFormatter

    valid_log_levels = sorted(cast(List[str], literal_to_list(LogLevel)))
    valid_log_formats = sorted(cast(List[str], literal_to_list(LogFormat)))

    parser = argparse.ArgumentParser(*args, **kwargs)
    monkey_patch_parser(parser)

    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        type=YAMLConfigFile,
        help=(
            "Absolute or relative path to a YAML file that contains this"
            " application's configuration."
        ),
    )
    parser.add_argument(
        "-L",
        "--log",
        metavar="FILE[:LEVEL][@FORMAT]",
        dest="logs",
        action="append",
        nargs="?",
        const="+",
        type=_log_type_factory(app_name),
        help=(
            "This option can be used to enable a new logging handler. FILE"
            " should be either a path to a logfile or one of the following"
            " special file types: [1] 'stderr' to log to standard error"
            " (enabled by default), [2] 'stdout' to log to standard out, [3]"
            " 'null' to disable all console (e.g. stderr) handlers, or [4]"
            " '+[NAME]' to choose a default logfile path (where NAME is an"
            " optional basename for the logfile). LEVEL can be any valid log"
            f" level (i.e. one of {valid_log_levels}) and FORMAT can be any"
            f" valid log format (i.e. one of {valid_log_formats}). NOTE: This"
            " option can be specified multiple times and has a default"
            " argument of %(const)r."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help=(
            "How verbose should the output be? This option can be specified"
            " multiple times (e.g. -v, -vv, -vvv, ...)."
        ),
    )

    caller_module = inspect.getmodule(frame)
    caller_dist_name = _get_distribution_name(caller_module)
    caller_file = getattr(caller_module, "__file__", None)
    if caller_dist_name and caller_file:
        assert caller_module is not None
        try:
            package_version = get_version(caller_dist_name)
            version = f"{caller_dist_name} {package_version}"

            package_location = _get_package_location(
                caller_file, caller_dist_name
            )
            version += f"\n    from {package_location}"

            while stack:
                exe_fname = stack.pop(0).filename
                if os.access(exe_fname, os.X_OK):
                    version += f"\n    by {_shorten_homedir(exe_fname)}"
                    break

            pyversion = ".".join(str(x) for x in sys.version_info[:3])
            version += f"\n    using Python {pyversion}"

            try:
                clack_version = get_version(__package__)
            except PackageNotFoundError:
                from . import __version__

                clack_version = __version__

            version += f"\n{__package__} {clack_version}"

            clack_location = _get_package_location(__file__, __package__)
            version += f"\n    from {clack_location}"

            parser.add_argument("--version", action="version", version=version)
        except PackageNotFoundError:
            pass

    return parser


def _get_distribution_name(module: ModuleType | None) -> str | None:
    """
    Retrieves the PyPI distribution name associated with a given module.

    Args:
        module: The module object for which to find the distribution.

    Returns:
        The PyPI distribution name, or None if not found.
    """
    if module is None:
        return None

    try:
        # Attempt to get the distribution metadata directly using the module name
        distribution = importlib.metadata.distribution(module.__name__)
        return distribution.metadata["Name"]
    except importlib.metadata.PackageNotFoundError:
        # Fallback logic: For packages where the module name might not
        # directly match the distribution name, try finding distributions
        # that contain this module
        for dist in importlib.metadata.distributions():
            module_names = dist.read_text("top_level.txt")
            if (
                module_names is not None
                and module.__package__ in module_names.splitlines()
            ):
                return dist.metadata["Name"]
        return None  # Distribution not found


def monkey_patch_parser(parser: argparse.ArgumentParser) -> None:
    """Tweeks ArgumentParser a bit so it works better with clack."""
    _patch_add_argument_method(parser)


def _patch_add_argument_method(parser: argparse.ArgumentParser) -> None:
    def add_argument(*args: Any, **kwargs: Any) -> None:
        if "default" not in kwargs:
            field_name = _get_field_name(args, kwargs)
            config_defaults = dyn.get_config_defaults()
            default = config_defaults.get(
                field_name, ARGPARSE_ARGUMENT_DEFAULT
            )
            kwargs["default"] = default

        argparse.ArgumentParser.add_argument(parser, *args, **kwargs)

    parser.add_argument = add_argument  # type: ignore[assignment]


def _get_field_name(args: Sequence[str], kwargs: Mapping[str, Any]) -> str:
    if dest := kwargs.get("dest", None):
        assert isinstance(dest, str)
        return dest

    if not args[0].startswith("-"):
        return args[0]

    long_opt = args[0]
    if not long_opt.startswith("--"):
        long_opt = args[1]

    return long_opt.lstrip("-").replace("-", "_")


def _log_type_factory(app_name: str) -> Callable[[str], Log]:
    def log_type(arg: str) -> Log:
        # This regex will match arguments of the form 'FILE[:LEVEL][@FORMAT]'.
        pttrn = (
            r"^(?P<file>[^:@]+)(?::(?P<level>[^:@]+))?(?:@(?P<format>[^:@]+))?"
        )
        match = re.match(pttrn, arg)
        if not match:
            raise argparse.ArgumentTypeError(
                f"Bad log specification ({arg!r}). Must match the following"
                f" regular expression: {pttrn!r}"
            )

        file = match.group("file")
        # If FILE is of the form '+[NAME]'...
        if file.startswith("+"):
            # Then we use a default logfile location.
            logfile_stem = file[1:]
            if not logfile_stem:
                logfile_stem = app_name
            file = str(get_default_logfile(logfile_stem))

        # If `--log null` is specified on the command-line...
        if file == "null":
            # HACK: The intention here is to disable logging to the console
            # (i.e. 'stderr' or 'stdout'). The actual effect is that only
            # CRITICAL logging messages will get logged to stderr. This
            # approaches a real solution since CRITICAL is used so infrequently
            # in practice, but is not technically correct.
            return Log(file="stderr", format="nocolor", level="CRITICAL")

        format_ = cast(Optional[LogFormat], match.group("format"))
        # If format is unset and this is a console logger...
        if format_ is None and file in ["stdout", "stderr"]:
            format_ = "color"
        # Else if format is unset and this is a file logger...
        elif format_ is None:
            format_ = "json"

        level = cast(Optional[LogLevel], match.group("level"))
        if level is not None:
            level = cast(LogLevel, level.upper())

        return Log(file=file, format=format_, level=level)

    return log_type


def _get_package_location(file_path: str, package: str) -> str:
    file_parent = Path(file_path).parent
    result = str(file_parent)

    package_subpath = package.replace(".", "/")
    result = "".join(result.rsplit(package_subpath, 1))

    result = _shorten_homedir(result)
    result = result.rstrip("/")

    return result


def _shorten_homedir(path: str) -> str:
    home = str(Path.home())
    return path.replace(home, "~")


class _HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Custom argparse.HelpFormatter that uses raw descriptions and sorts optional
    arguments alphabetically.
    """

    def add_arguments(self, actions: Iterable[argparse.Action]) -> None:
        actions = sorted(actions, key=_argparse_action_key)
        super().add_arguments(actions)


def _argparse_action_key(action: argparse.Action) -> str:
    opts = action.option_strings
    if opts:
        return opts[-1].lstrip("-")
    else:
        return action.dest
