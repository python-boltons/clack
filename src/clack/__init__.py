"""(C)ommand (L)ine (A)pplication (C)onfig (K)it

A wrapper around the `argparse` library that aims to handle _all_ application
configuration.
"""

import logging as _logging

from . import xdg
from ._config import Config
from ._config_file import ConfigFile, YAMLConfigFile
from ._helpers import NewCommand, comma_list_or_file, new_command_factory
from ._main import MainType, main_factory
from ._parser import Parser, filter_cli_args


__all__ = [
    "Config",
    "ConfigFile",
    "MainType",
    "NewCommand",
    "Parser",
    "YAMLConfigFile",
    "comma_list_or_file",
    "filter_cli_args",
    "main_factory",
    "new_command_factory",
    "xdg",
]

__author__ = "Bryan M Bugyi"
__email__ = "bryanbugyi34@gmail.com"
__version__ = "0.2.7"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
