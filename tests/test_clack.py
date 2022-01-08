"""Miscellaneous tests for the clack library."""

from eris import Err
import pytest

import clack
from clack import _dynvars as dyn
from clack.pytest_plugin import MakeConfigFile

from .shared import Config


def test_new_command_factory() -> None:
    """Test the clack.new_command_factory() function."""
    with dyn.clack_envvars_set("test_clack", [Config]):  # type: ignore[list-item]
        parser = clack.Parser()
        new_command = clack.new_command_factory(parser, dest="command")
        foo = new_command("foo", help="Test FOO subcommand.")

        foo.add_argument("--bar", action="store_true", help="Test BAR option.")

        args = parser.parse_args(["foo", "--bar"])

        assert args.command == "foo"
        assert args.bar


def test_config_is_immutable() -> None:
    """Test that the Config object's attributes are immutable."""
    with dyn.clack_envvars_set("test_clack", [Config]):  # type: ignore[list-item]
        cfg = Config.from_cli_args(["", "--do-stuff"])
        assert cfg.do_stuff

        with pytest.raises(TypeError):
            cfg.do_stuff = False


def test_config_file(make_config_file: MakeConfigFile) -> None:
    """Test the clack.ConfigFile protocol implementations."""
    cf = make_config_file("clack.yml", foo="FOO", bar=3, baz=False)

    assert sorted(cf.to_dict().unwrap().items()) == [
        ("bar", 3),
        ("baz", False),
        ("foo", "FOO"),
    ]

    assert cf.get("foo").unwrap() == "FOO"
    assert cf.set("foo", "KUNG").unwrap() == "FOO"
    assert isinstance(cf.set("fool", "FOOL"), Err)

    assert cf.set("fool", "FOOL", allow_new=True).unwrap() is None
    assert sorted(cf.to_dict().unwrap().items()) == [
        ("bar", 3),
        ("baz", False),
        ("foo", "KUNG"),
        ("fool", "FOOL"),
    ]
