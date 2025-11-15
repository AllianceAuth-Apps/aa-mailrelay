# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

## [2.0.0] - 2025-11-15

### Changed

- BREAKING CHANGE: Support dropped for AA3
- Added support for Python 3.12

## [1.4.0] - 2024-05-10

### Added

- Ability to configure custom host & port for discordproxy via new settings: `DISCORDPROXY_HOST`, `DISCORDPROXY_PORT`

### Changed

- Consolidated timeout settings for user and tasks into one

## [1.3.0] - 2024-01-18

### Changed

- Add support for AA 4

## [1.2.0] - 2023-12-08

### Changed

- Ability to disable `MAILRELAY_OLDEST_MAIL_HOURS` setting
- Removed dependencies to Member Audit mail update sub-tasks
- Fixed some minor model issues
- Minimum supported Python version is now 3.8

### Fixed

- CI tests for Python 3.10 & 3.11 are not running

## [1.1.0] - 2023-07-18

### Added

- Support for Python 3.10
- Support for Python 3.11
- Add pylint to CI pipeline

### Changed

- Migrated project config to PEP 621
- Migrate to AA 3, dropped support for AA2
- Dropped support for Python 3.7
- Action for resending mails now always available (not only in DEBUG mode)

## [1.0.4] - 2022-07-24

### Fixed

- Will now work with both Member Audit 1.16 and older versions

## [1.0.3] - 2022-06-17

### Changed

- Add PyPI wheel

## [1.0.2] - 2022-03-02

### Changed

- Update dependencies for AA 3 compatibility
- Migrations update required for Django 4

## [1.0.1] - 2022-02-11

### Fixed

- Can not deal with non-latin scripts

## [1.0.0] - 2022-02-11

### Added

- Now supports most eve link types

### Fixed

- Links are not rendered correctly

## [1.0.0b2] - 2022-01-03

### Fixed

- ping/relay not formatting the @ everyone (#1)
- Show message when fetching channels failed as warning, not success

## [1.0.0b1] - 2022-01-02

### Added

- Initial release as BETA

### Changed

### Fixed
