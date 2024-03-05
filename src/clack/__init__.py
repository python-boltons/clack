"""(C)ommand (L)ine (A)pplication (C)onfig (K)it

A wrapper around the `argparse` library that aims to handle _all_ application
configuration.
"""

import logging as _logging

from . import types, xdg
from ._config import Config
from ._config_file import YAMLConfigFile
from ._dynvars import get_config
from ._helpers import (
    comma_list_or_file,
    filter_cli_args,
    new_command_factory,
    register_runner_factory,
)
from ._main import main_factory
from ._parser import Parser


__all__ = [
    "Config",
    "Parser",
    "YAMLConfigFile",
    "comma_list_or_file",
    "filter_cli_args",
    "get_config",
    "main_factory",
    "new_command_factory",
    "register_runner_factory",
    "types",
    "xdg",
]

__author__ = "Bryan M Bugyi"
__email__ = "bryanbugyi34@gmail.com"
__version__ = "0.3.6"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
