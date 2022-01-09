"""Helper classes/functions for the tests contained in test_e2e.py."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import (
    Dict,
    Final,
    Iterable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Type,
    cast,
)

from logrus import Logger
from typist import PathLike

from clack import xdg
from clack.types import ClackConfigFile


logger = Logger(__name__)

CLI_ARGS_MARK: Final = "ARGS"
CONFIG_MARK: Final = "CONFIG"
ENV_MARK: Final = "ENV"
OUTPUT_MARK: Final = "OUTPUT"
START_MARK_PREFIX: Final = "# TEST |"


class Case(NamedTuple):
    """A Test Case.

    Each Case object represents a single test case comment block.
    """

    name: str
    cli_args: List[str]
    output: str
    env: Optional[Dict[str, str]]

    @classmethod
    def from_comment_lines(
        cls,
        config_file_type: Type[ClackConfigFile],
        app_name: str,
        lines: Sequence[str],
    ) -> Case:
        """Constructs a Case object from a single test case's comment lines."""
        log = logger.bind_fargs(locals())

        assert lines[0].startswith(START_MARK_PREFIX)
        name = lines[0].replace(START_MARK_PREFIX, "").strip(" ")

        cli_args: Optional[List[str]] = None
        output: Optional[str] = None
        env: Optional[Dict[str, str]] = None
        for line in lines:
            if line.startswith("###"):
                log.info("Skipping START/END marker.", line=line)
                continue

            line = line.lstrip("# ")
            if ":" not in line:
                log.info("Skipping line which doesn't contain ':'.", line=line)
                continue

            key, value = line.split(":", maxsplit=1)
            key = key.upper()
            value = value.lstrip(" ")

            if key == CLI_ARGS_MARK:
                cli_args = value.split(" ")
            elif key == OUTPUT_MARK:
                output = value
            elif key == ENV_MARK:
                env_list = cast(
                    List[Tuple[str, str]],
                    [tuple(v.split("=")) for v in value.split(" ")],
                )
                env = dict(env_list)
            elif key == CONFIG_MARK:
                filename, json_data = value.split(" ", maxsplit=1)
                filename = filename.replace(
                    "XDG", str(xdg.get_full_dir("config", app_name))
                )
                config_dict = json.loads(json_data)

                path = Path(filename)
                config_file_type.new(path, **config_dict)
            else:
                log.warning("Unrecognized key.", key=key, value=value)

        assert (
            cli_args is not None
        ), f"No ARGS defined for the {name!r} test case.\n\n{lines!r}"
        assert (
            output is not None
        ), f"No OUTPUT defined for the {name!r} test case.\n\n{lines!r}"

        return cls(name, cli_args, output, env)


def case_comments_from_lines(lines: Iterable[str]) -> List[List[str]]:
    """Constructs a list of Case comment blocks from a file's contents.

    Args:
        lines: A file's contents represented as a list of lines.

    Returns:
        A list of lists of "comment lines" that can be passed into
        Case.from_comment_lines().
    """
    result: List[List[str]] = []

    in_test_case = False
    for line in lines:
        line = line.strip()

        if line.startswith(START_MARK_PREFIX):
            result.append([])
            in_test_case = True
        elif not line.startswith("#"):
            in_test_case = False

        if in_test_case:
            result[-1].append(line)

    return result


@contextmanager
def envvars_set(env_map: Optional[Mapping[str, str]]) -> Iterator[None]:
    """Sets environment variable values while in this context ONLY."""
    if env_map is None:
        yield
    else:
        old_env_dict: Dict[str, str] = {}
        for key, value in env_map.items():
            if key in os.environ:
                old_env_dict[key] = os.environ[key]

            os.environ[key] = value

        yield

        for key in env_map:
            if key in old_env_dict:
                os.environ[key] = old_env_dict[key]
            else:
                del os.environ[key]


@contextmanager
def dir_context(new_cwd: PathLike) -> Iterator[None]:
    """Chdir to ``new_cwd`` while in this context ONLY."""
    new_cwd = Path(new_cwd)
    old_cwd = os.getcwd()
    os.chdir(new_cwd)

    yield

    os.chdir(old_cwd)
