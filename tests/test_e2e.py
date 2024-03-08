"""End-to-End (E2E) tests using dummy applications."""

from __future__ import annotations

from pathlib import Path
import shutil
from types import ModuleType
from typing import List, Type

from _pytest.capture import CaptureFixture
from _pytest.tmpdir import TempPathFactory
from logrus import Logger
from pytest import mark

from clack import YAMLConfigFile
from clack.types import ClackConfigFile, ClackMain

from .data.e2e import e2e_test_mods
from .e2e_helpers import (
    START_MARK_PREFIX,
    Case,
    case_comments_from_lines,
    dir_context,
    envvars_set,
)


logger = Logger(__name__)
params = mark.parametrize


@params("mod", e2e_test_mods)
@params("config_file_type", [YAMLConfigFile])
def test_end_to_end(
    tmp_path_factory: TempPathFactory,
    capsys: CaptureFixture,
    mod: ModuleType,
    config_file_type: Type[ClackConfigFile],
) -> None:
    """Tests the mini-applications defined in tests/data/e2e."""
    log = logger.bind(mod=mod)

    mod_name = mod.__name__.rsplit(".", maxsplit=1)[-1]
    mod_file = mod.__file__
    assert mod_file is not None

    mod_path = Path(mod_file)
    log.info("Loading test cases from dummy application.", mod_path=mod_path)
    lines = mod_path.read_text().split("\n")
    all_comment_lines = case_comments_from_lines(lines)
    for comment_lines in all_comment_lines:
        tmp_path = tmp_path_factory.mktemp(mod_name, numbered=False)
        tmp_xdg_config = tmp_path / ".config"
        tmp_xdg_config.mkdir(parents=True, exist_ok=True)

        with dir_context(tmp_path), envvars_set(
            {"XDG_CONFIG_HOME": str(tmp_xdg_config)}
        ):
            test_case = Case.from_comment_lines(
                config_file_type, mod_name, comment_lines
            )
            log.info("New test case.", test_case=test_case)

            main: ClackMain = getattr(mod, "main")
            with envvars_set(test_case.env):
                ec = main([mod_name] + test_case.cli_args)

            assert ec == 0

            capture = capsys.readouterr()
            assert capture.out.strip() == test_case.output

        shutil.rmtree(tmp_path)


@params(
    "name,lines,expected",
    [(
        "1",
        ["# ARGS: --foo=FOO --bar 2", "# OUTPUT: foobar"],
        Case("1", ["--foo=FOO", "--bar", "2"], "foobar", None),
    )],
)
def test_from_comment_lines(
    name: str, lines: List[str], expected: Case
) -> None:
    """Tests the Case.from_comment_lines() constructor method."""
    lines = [START_MARK_PREFIX + f" {name}"] + lines
    actual = Case.from_comment_lines(YAMLConfigFile, "test_e2e", lines)
    assert actual == expected
