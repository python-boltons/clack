"""clack package

command-line application configuration kit (CLACK)... A wrapper around the
`argparse` library that aims to handle _all_ application configuration.
"""

import logging as _logging

from ._core import dummy


__all__ = ["dummy"]

__author__ = "Bryan M Bugyi"
__email__ = "bryanbugyi34@gmail.com"
__version__ = "0.0.1"

_logging.getLogger(__name__).addHandler(_logging.NullHandler())
