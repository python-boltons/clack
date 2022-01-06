# Changelog for `clack`

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to
[Semantic Versioning].

[Keep a Changelog]: https://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: https://semver.org/


## [Unreleased](https://github.com/python-boltons/clack/compare/0.2.1...HEAD)

No notable changes have been made.


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
