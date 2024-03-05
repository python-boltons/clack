"""Contains the ClackConfigFile protocol's implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from eris import ErisError, Err, Ok, Result, return_lazy_result
from typist import PathLike
import yaml


class YAMLConfigFile:
    """A clack YAML configuration file.

    This class is useful as a way to conveniently get/set configuration values
    in/to your current application's config file.
    """

    extensions = ["yml", "yaml"]

    def __init__(self, path: PathLike) -> None:
        self.path = Path(path)

    def __repr__(self) -> str:  # noqa: D105
        return f"{self.__class__.__name__}({self.path})"

    def get(self, key: str) -> Result[Any, ErisError]:
        """Getter for values in this config file."""
        if not self.path.is_file():
            return Err(
                "This clack configuration file does NOT exist yet:"
                f" not_a_file={self.path}"
            )

        config_dict_result = self.to_dict()
        if isinstance(config_dict_result, Err):
            err: Err[Any, ErisError] = Err(
                "Unable to convert this config file into a dictionary."
            )
            return err.chain(config_dict_result)

        config_dict = config_dict_result.ok()
        try:
            return Ok(config_dict[key])
        except KeyError as e:
            err = Err(
                "The desired configuration key is not present in this config"
                f" file: key={key} config_dict={config_dict} self={self}"
            )
            return err.chain(e)

    @classmethod
    def new(cls, path: PathLike, **kwargs: Any) -> YAMLConfigFile:
        """Construct a new YAMLConfigFile object."""
        config_dict = {**kwargs}

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize config file...
        with path.open("w+") as f:
            yaml.dump(config_dict, f, allow_unicode=True)

        return cls(path)

    @return_lazy_result
    def set(
        self, key: str, value: Any, *, allow_new: bool = False
    ) -> Result[Any, ErisError]:
        """Setter for values in this config file."""
        if self.path.exists() and not self.path.is_file():
            return Err(
                f"This config file is NOT a file?: not_a_file={self.path}"
            )

        if not self.path.exists():
            if allow_new:
                with self.path.open("w+") as f:
                    yaml.dump({key: value}, f)
                    return Ok(None)
            else:
                return Err(
                    "This clack configuration file does NOT exist yet:"
                    f" not_a_file={self.path}"
                )

        old_value_result = self.get(key)
        old_value: Any
        if isinstance(old_value_result, Err):
            old_value = None
        else:
            old_value = old_value_result.ok()

        new_lines = []
        new_line = key + ': "' + str(value) + '"'
        found_key = False
        for line in self.path.read_text().split("\n"):
            line = line.rstrip()
            if line.startswith(key + ":"):
                found_key = True
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        if not found_key:
            if allow_new:
                new_lines[-1] = new_line
            else:
                return Err(
                    f"The provided key does not exist. key={key} self={self}"
                )

        self.path.write_text("\n".join(new_lines))
        return Ok(old_value)

    def to_dict(self) -> Result[dict[str, Any], ErisError]:
        """Converts this configuration file into a dict."""
        if not self.path.is_file():
            return Err(
                "This clack configuration file does NOT exist yet:"
                f" not_a_file={self.path}"
            )

        result: Dict[str, Any] = yaml.safe_load(self.path.read_bytes())
        return Ok(result)
