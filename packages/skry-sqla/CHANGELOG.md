# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-09

- Added typed `AsyncRepository` abstraction for async SQLAlchemy models.
- Improved `AsyncEntityManager`:
  - added `list` helper
  - fixed async `delete` handling
  - added `insert_many` (and backward-compatible `insert_mamy` alias)
  - normalized transactional rollback behavior
- Added package exceptions: `SkrySqlaError`, `PersistenceError`.
- Expanded and stabilized package public API exports.
- Added `py.typed` marker for PEP 561 type distribution.
- Added repository/API tests for CRUD, bulk insert, and rollback behavior.
- Added workspace quality tooling configuration: `ruff`, `mypy`, `pytest-cov`.
