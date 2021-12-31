"""Helper classes/functions for the tests contained in test_e2e.py."""

from __future__ import annotations

from contextlib import contextmanager
import os
from typing import (
    Dict,
    Final,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    cast,
)

from logrus import Logger


logger = Logger(__name__)

CLI_ARGS_MARK: Final = "ARGS"
END_MARK: Final = "### END TEST CASE"
ENV_MARK: Final = "ENV"
OUTPUT_MARK: Final = "OUTPUT"
START_MARK_PREFIX: Final = "### TEST CASE"


class Case(NamedTuple):
    """A Test Case.

    Each Case object represents a single test case comment block.
    """

    name: str
    cli_args: List[str]
    output: str
    env: Optional[Dict[str, str]]

    @classmethod
    def from_comment_lines(cls, lines: Sequence[str]) -> Case:
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

            key, value = line.split(":")
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
    """Constructs a list of Case objects from a file's lines."""
    result: List[List[str]] = []

    in_test_case = False
    for line in lines:
        line = line.strip()

        if line.startswith(START_MARK_PREFIX):
            result.append([])
            in_test_case = True

        if in_test_case:
            result[-1].append(line)

        if line == END_MARK:
            in_test_case = False

    return result


@contextmanager
def envvars_set(env_dict: Optional[Dict[str, str]]) -> Iterator[None]:
    """Context manager that sets environment variable values temporarily."""
    if env_dict is None:
        yield
    else:
        old_envvar_map: Dict[str, str] = {}
        for envvar, value in env_dict.items():
            if envvar in os.environ:
                old_envvar_map[envvar] = os.environ[envvar]

            os.environ[envvar] = value

        yield

        for envvar in env_dict:
            if envvar in old_envvar_map:
                os.environ[envvar] = old_envvar_map[envvar]
            else:
                del os.environ[envvar]
