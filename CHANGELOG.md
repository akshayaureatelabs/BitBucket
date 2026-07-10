# Changelog

All notable changes to the BitBucket Pipeline QA & Utility Suite are documented in this file.

**Author:** Sr. QA Tester - Akshaykumar Dudhwala

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.1.0] - 2026-06-29

### Fixed

#### Critical (4)
- **All 4 tools** — `base_dir = Path(__file__).parent.parent` resolved to the wrong directory (`QA Scripts/` instead of `BitBucket/`), breaking all file path lookups. Changed to `Path(__file__).parent`.
- **`performance_benchmark.py`** — `--check-regressions` had `default=10.0` which is always truthy, causing regression checks to fire on every invocation. Changed default to `None` with `is not None` guard.
- **`dependency_health.py`** — `_parse_requirements()` included upper bounds in version strings (e.g., `2.0.3,<3.0.0`). Added `.split(',')[0].strip()` to extract only the lower bound.
- **`pipeline_dashboard.py`** — `INSERT OR REPLACE` on `pipeline_runs` but plain `INSERT` on child tables created orphaned rows on re-record. Now deletes existing child rows before inserting.

#### Medium (4)
- **`smart_test_selector.py`** — `tests_dir.rglob()` called without existence check in `generate_test_matrix()` else branch. Added `tests_dir.exists()` guard.
- **`performance_benchmark.py`** — `tracemalloc.start()` called on every decorated function invocation, resetting memory tracking. Added `tracemalloc.is_tracing()` guard so it only starts/stops if we own it.
- **`dependency_health.py`** — PyUp API returns 403 without authentication, silently failing. Now wraps the call in try/except and logs a debug message on 403.
- **`test_precheck.py`** — `test_requirements_exists` and `test_pipeline_yml_exists` failed when pytest CWD != project directory. Changed to use `os.path.join(BASE_DIR, ...)`.

### Changed

- **All 4 tools** — Migrated all `print()` calls to Python `logging` module with `logging.basicConfig()` in each `main()`. Uses `logger.info()`, `logger.warning()`, and `logger.error()` with `%`-style format strings for performance.
- **`dependency_health.py`** — Added `pypistats_cache.json` with 24h TTL to avoid 28 redundant HTTP calls per run. Cache is loaded on init, checked before API calls, and persisted via `_save_caches()` after `check_all_packages()`.
- **`dependency_health.py`** — Replaced bare `except: pass` in `calculate_health_score()` with `except (requests.RequestException, ValueError, KeyError)` with `logger.debug()`.
- **`dependency_health.py`**, **`performance_benchmark.py`** — Added `html_module.escape()` on all user-controlled strings in HTML report generation to prevent XSS injection.
- **`dependency_health.py`** — Added `_strip_extras()` static method to handle `package[extra]>=1.0` syntax in requirements parsing. Refactored `_parse_requirements()` to use a loop over version specifiers.
- **`PROJECT_OVERVIEW.md`** — Updated to v1.1.0, documented all 21 bug fixes, added pypistats cache to artifacts table, updated testing strategy.

### Added
- **`tests/test_fixes.py`** — 13 dedicated unit tests covering:
  - `TestStripExtras` (6 tests) — extras parsing edge cases
  - `TestPypistatsCaching` (4 tests) — cache hit/miss, stale/fresh cache behavior
  - `TestTracemallocGuard` (3 tests) — external tracemalloc preservation, auto start/stop, result recording

### Removed
- Dead `import re` that was accidentally added during earlier edits.

---

## [1.0.0] - 2026-06-26

### Initial Release

#### Features
- **Smart Test Selector** — Analyzes git diffs to run only affected tests, generates `test-matrix.json` for parallel CI execution
- **Performance Benchmark** — Tracks execution time, memory, and CPU; compares against baselines to detect regressions
- **Dependency Health Check** — Monitors packages for outdated versions and known vulnerabilities via PyPI, OSV.dev, and PyUp APIs
- **Pipeline Dashboard** — Records pipeline metrics to SQLite and generates interactive Plotly-based HTML dashboard

#### CI/CD Pipeline
- 6-stage BitBucket Pipeline with 11 steps
- Full pipeline on PRs and `main`; quick validation on feature branches
- 85% minimum test coverage enforced
- Parallel execution with caching

#### Quality Tools
- Linting: black, isort, flake8, pylint
- Type checking: mypy (strict mode)
- Security scanning: bandit, pip-audit
- Complexity analysis: radon, vulture

#### Setup
- Cross-platform one-click setup scripts (`setup.bat`, `setup.sh`, `setup_all.py`)
- 28 Python dependencies with bounded version ranges (`>=X,<Y`)

#### Known Issues (fixed in 1.1.0)
- `base_dir` resolves to wrong directory in all 4 tools
- `--check-regressions` fires on every run regardless of flag
- Version parsing includes upper bounds from bounded ranges
- `tracemalloc` restarts on every decorated function call
- HTML reports lack XSS escaping
- pypistats API called with no caching (28 HTTP calls per run)
- Bare `except: pass` swallows all errors
- `print()` used throughout instead of logging
- Test failures when CWD != project directory
