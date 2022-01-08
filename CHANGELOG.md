# Changelog for `clack`

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to
[Semantic Versioning].

[Keep a Changelog]: https://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: https://semver.org/


## [Unreleased](https://github.com/python-boltons/clack/compare/0.2.8...HEAD)

No notable changes have been made.


## [0.2.8](https://github.com/python-boltons/clack/compare/0.2.7...0.2.8) - 2022-01-08

### Fixed

* Add 'path' attribute to `ConfigFile` Protocol.


## [0.2.7](https://github.com/python-boltons/clack/compare/0.2.6...0.2.7) - 2022-01-08

### Miscellaneous

* Abstract away all YAML logic to `ConfigFile` Protocol.


## [0.2.6](https://github.com/python-boltons/clack/compare/0.2.5...0.2.6) - 2022-01-08

### Added

* Add `clack.ConfigFile` class (the new default for the `--config` option).
* Add `clack.pytest_plugin` that includes `make_config_file()` fixture.


## [0.2.5](https://github.com/python-boltons/clack/compare/0.2.4...0.2.5) - 2022-01-08

### Changed

* Set the `Config.config_file` attribute for implicit config files too.


## [0.2.4](https://github.com/python-boltons/clack/compare/0.2.3...0.2.4) - 2022-01-08

### Fixed

* Fix bug with new `--config` CLI option parsing.


## [0.2.3](https://github.com/python-boltons/clack/compare/0.2.2...0.2.3) - 2022-01-08

### Added

* Add support for explicit config file locations via the new `--config` CLI option.


## [0.2.2](https://github.com/python-boltons/clack/compare/0.2.1...0.2.2) - 2022-01-06

### Fixed

* Allow `clack.Config` to have extra arguments.


## [0.2.1](https://github.com/python-boltons/clack/compare/0.2.0...0.2.1) - 2022-01-06

### Fixed

* Fix crash when `Config` defaults are not json-serializable.


## [0.2.0](https://github.com/python-boltons/clack/compare/0.1.3...0.2.0) - 2022-01-04

### Added

* Ability to load `Config()` class values from environment variables.
* Ability to load `Config()` class values from YAML configuration files.

### Changed

* *BREAKING CHANGE*: The signature of the `clack.main_factory()` function has
  been changed.

### Miscellaneous

* Increased test coverage to >=80%.


## [0.1.3](https://github.com/python-boltons/clack/compare/0.1.2...0.1.3) - 2021-12-26

### Added

* Add `comma_list_or_file` class.


## [0.1.2](https://github.com/python-boltons/clack/compare/0.1.1...0.1.2) - 2021-12-25

### Added

* Add new `clack.xdg` module.


## [0.1.1](https://github.com/python-boltons/clack/compare/0.1.0...0.1.1) - 2021-12-24

### Fixed

* Fix type checking issue with `clack.main_factory()`.


## [0.1.0](https://github.com/python-boltons/clack/releases/tag/0.1.0) - 2021-12-23

### Miscellaneous

* Port `clack` library from (original) `bugyi-lib` library.
* First release.
