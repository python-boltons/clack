"""XDG Utilities"""

import os
from pathlib import Path
from typing import Dict, Literal, Tuple


XDG_Type = Literal["cache", "config", "data", "runtime"]

_HOME = os.environ.get("HOME")
# Mapping of XDG directory types to 2-tuples of the form (envvar, default_dir).
_XDG_TYPE_MAP: Dict[XDG_Type, Tuple[str, str]] = {
    "cache": ("XDG_CACHE_HOME", f"{_HOME}/.cache"),
    "config": ("XDG_CONFIG_HOME", f"{_HOME}/.config"),
    "data": ("XDG_DATA_HOME", f"{_HOME}/.local/share"),
    "runtime": ("XDG_RUNTIME_DIR", "/tmp"),
}


def init_full_dir(xdg_type: XDG_Type, app_name: str) -> Path:
    """
    Returns:
        Full XDG user directory (including scriptname).

    Side Effects:
        Ensures the full XDG user directory exists before returning it.
    """
    full_xdg_dir = get_full_dir(xdg_type, app_name)
    full_xdg_dir.mkdir(parents=True, exist_ok=True)
    return full_xdg_dir


def get_full_dir(xdg_type: XDG_Type, app_name: str) -> Path:
    """
    Returns:
        Full XDG user directory (including scriptname).
    """
    base_xdg_dir = get_base_dir(xdg_type)
    full_xdg_dir = base_xdg_dir / app_name
    return full_xdg_dir


def get_base_dir(xdg_type: XDG_Type) -> Path:
    """
    Returns:
        The base/general XDG user directory.
    """
    assert (
        xdg_type in _XDG_TYPE_MAP
    ), "Provided @xdg_type parameter is not valid: {!r} not in {}".format(
        xdg_type, list(_XDG_TYPE_MAP.keys())
    )

    envvar, default_dir = _XDG_TYPE_MAP[xdg_type]
    xdg_dir = Path(os.environ.get(envvar, default_dir))
    return xdg_dir
