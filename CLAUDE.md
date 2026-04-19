# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Archivooor — Python CLI + library for submitting web pages to the Wayback Machine (archive.org). Uses multithreaded batch archival with automatic retries.

## Commands

```bash
make install-dev          # install all deps (uv sync --all-extras --dev)
make lint                 # ruff check --fix + mypy archivooor
uv run archivooor --help  # run CLI
uv run ruff check --fix   # lint only
uv run ruff format        # format only
uv run mypy archivooor    # type check only
```

No unit test suite exists. CI runs CLI integration checks (help output, keyring set/delete) across Python 3.9–3.13 on ubuntu/macos/windows.

## Architecture

All source lives in `archivooor/`:

- **`archiver.py`** — Core logic. `Archiver` class handles save/status API calls with S3 auth headers. `NetworkHandler` wraps requests.Session with urllib3 retry (5 retries, exponential backoff). `Sitemap` parses XML sitemaps into URL lists. `save_pages()` uses ThreadPoolExecutor (5 workers) with recursive retry on failures.
- **`cli.py`** — Click CLI. Commands: `save`, `job`, `stats`, `keys set`, `keys delete`. Loads credentials via `key_utils` in the group callback.
- **`key_utils.py`** — Credential resolution: env vars (`s3_access_key`, `s3_secret_key`) checked first, then system keyring fallback.
- **`exceptions.py`** — Single `ArchivooorException` base class.

## Credentials

Set env vars `s3_access_key` and `s3_secret_key`, or store via CLI:
```bash
archivooor keys set <access_key> <secret_key>
```
Env vars take precedence over keyring. Credentials are loaded on every CLI invocation (in the Click group callback).

## Release

Bump version in `pyproject.toml`, then push a tag matching `v[0-9]+.[0-9]+.[0-9]+`. CI builds with `uv build` and publishes to PyPI.

## Tooling

- **Package manager**: uv (hatchling build backend)
- **Linter/formatter**: ruff (isort rules enabled)
- **Type checker**: mypy
- **Git hooks**: prek (trailing-whitespace, end-of-file-fixer, no-commit-to-branch, ruff, ruff-format, uv-lock)

## Gotchas

- **no-commit-to-branch**: prek hook blocks direct commits to `main`. Work on feature branches.
- **`save_pages` recursive retry**: On failure, retries the failed subset recursively up to `MAX_RETRIES` (3) with exponential backoff. After max retries, returns error dicts for remaining URLs.
