"""Miscellaneous tests for the clack library."""

import pytest

import clack
from clack._dynvars import clack_envvars_set

from .shared import Config


def test_new_command_factory() -> None:
    """Test the clack.new_command_factory() function."""
    with clack_envvars_set("test_clack", Config):
        parser = clack.Parser()

    new_command = clack.new_command_factory(parser, dest="command")

    foo = new_command("foo", help="Test FOO subcommand.")
    foo.add_argument("--bar", action="store_true", help="Test BAR option.")

    args = parser.parse_args(["foo", "--bar"])
    assert args.command == "foo"
    assert args.bar


def test_config_is_immutable() -> None:
    """Test that the Config object's attributes are immutable."""
    with clack_envvars_set("test_clack", Config):
        cfg = Config.from_cli_args(["", "--do-stuff"])
        assert cfg.do_stuff

        with pytest.raises(TypeError):
            cfg.do_stuff = False
