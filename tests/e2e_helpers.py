"""Helper classes/functions for the tests contained in test_e2e.py."""

from __future__ import annotations

from typing import Final, Iterable, List, NamedTuple, Optional, Sequence

from logrus import Logger


logger = Logger(__name__)

CLI_ARGS_MARK: Final = "ARGS"
END_MARK: Final = "### END TEST CASE"
OUTPUT_MARK: Final = "OUTPUT"
START_MARK_PREFIX: Final = "### TEST CASE"


class Case(NamedTuple):
    """A Test Case.

    Each Case object represents a single test case comment block.
    """

    name: str
    cli_args: List[str]
    output: str

    @classmethod
    def from_comment_lines(cls, lines: Sequence[str]) -> Case:
        """Constructs a Case object from a single test case's comment lines."""
        log = logger.bind_fargs(locals())

        assert lines[0].startswith(START_MARK_PREFIX)
        name = lines[0].replace(START_MARK_PREFIX, "").strip(" ")

        cli_args: Optional[List[str]] = None
        output: Optional[str] = None
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
            else:
                log.warning("Unrecognized key.", key=key, value=value)

        assert (
            cli_args is not None
        ), f"No ARGS defined for the {name!r} test case.\n\n{lines!r}"
        assert (
            output is not None
        ), f"No OUTPUT defined for the {name!r} test case.\n\n{lines!r}"

        return cls(name, cli_args, output)


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

        if line.strip() == END_MARK:
            in_test_case = False

    return result
