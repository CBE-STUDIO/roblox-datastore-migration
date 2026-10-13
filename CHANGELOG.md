# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-10-13

### Added
- First public release of the Roblox DataStore Migration Toolkit.
- Read-only backup of an entire old experience's DataStores (`old_backup.py`).
- Automatic retry of throttled / errored backup entries (`retry_errors.py`).
- Migration-plan builder with safe merge rules (`build_ops.py`).
- Donation-board special-case merging (`board_fetch.py`).
- Resumable, multi-threaded migration engine (`migrate_oc.py`).
- Optional in-Studio worker for environments without full Open Cloud scopes
  (`migration_server.py` + `studio_plugin/`).
- Full beginner documentation (`docs/01`–`docs/10`).
- Apache-2.0 license, NOTICE, and CITATION files.
