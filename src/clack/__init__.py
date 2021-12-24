"""(C)ommand (L)ine (A)pplication (C)onfig (K)it

A wrapper around the `argparse` library that aims to handle _all_ application
configuration.
"""

import logging as _logging

from ._core import (
    AbstractConfig,
    Config,
    MainType,
    NewCommand,
    Parser,
    main_factory,
    new_command_factory,
)


__all__ = [
    "AbstractConfig",
    "Config",
    "MainType",
    "NewCommand",
    "Parser",
    "main_factory",
    "new_command_factory",
]

__author__ = "Bryan M Bugyi"
__email__ = "bryanbugyi34@gmail.com"
__version__ = "0.1.1"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
