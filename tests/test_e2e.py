"""End-to-End (E2E) tests using dummy applications."""

from __future__ import annotations

from pathlib import Path
from typing import List

from _pytest.capture import CaptureFixture
from logrus import Logger
from pytest import mark

from clack import MainType

from .data.e2e import e2e_test_mods
from .e2e_helpers import (
    END_MARK,
    START_MARK_PREFIX,
    Case,
    case_comments_from_lines,
    envvars_set,
)


logger = Logger(__name__)
params = mark.parametrize


def test_end_to_end(capsys: CaptureFixture) -> None:
    """Tests the mini-applications defined in tests/data/e2e."""
    for mod in e2e_test_mods:
        log = logger.bind(mod=mod)

        mod_path = Path(mod.__file__)
        log.info(
            "Loading test cases from dummy application.", mod_path=mod_path
        )
        lines = mod_path.read_text().split("\n")
        all_comment_lines = case_comments_from_lines(lines)
        for comment_lines in all_comment_lines:
            case = Case.from_comment_lines(comment_lines)
            log.info("New test case.", case=case)

            main: MainType = getattr(mod, "main")
            with envvars_set(case.env):
                ec = main([""] + case.cli_args)

            assert ec == 0

            capture = capsys.readouterr()
            assert capture.out.strip() == case.output


@params(
    "name,lines,expected",
    [
        (
            "1",
            ["# ARGS: --foo=FOO --bar 2", "# OUTPUT: foobar"],
            Case("1", ["--foo=FOO", "--bar", "2"], "foobar", None),
        )
    ],
)
def test_from_comment_lines(
    name: str, lines: List[str], expected: Case
) -> None:
    """Tests the Case.from_comment_lines() constructor method."""
    lines = [START_MARK_PREFIX + f" {name}"] + lines + [END_MARK]
    actual = Case.from_comment_lines(lines)
    assert actual == expected
