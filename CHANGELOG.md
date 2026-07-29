# Changelog

All notable changes to the BitBucket Pipeline QA & Utility Suite are documented in this file.

**Author:** Sr. QA Tester - Akshaykumar Dudhwala

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.5.6] - 2026-07-21

### Fixed
- `run_full_pipeline.bat` — Added ERRORLEVEL checks to steps 4/5/7/9 (security, complexity, benchmark, dashboard) — previously always reported PASS
- `setup_all.py` — Added per-file skip logging when `force=False`

### Changed
- `tests/test_quality_gate.py` — Added assertions to 3 previously assertion-less tests
- `tests/test_sample.py` — Refactored to parametrized import test with explicit assertion
- `setup_all.py` — Converted CRLF to LF line endings

### Removed
- Stale `aureatelabs-bannerslider-hyva` submodule reference from git tracking

---

## [1.5.5] - 2026-07-21

### Fixed
- **CRITICAL:** `_gen_setup.py` — Added `code_scanner.py` to EMBEDDED_FILES sources (hooks couldn't find scanner on fresh deploy)
- **CRITICAL:** `setup_all.py` — Regenerated to sync all 20 embedded files (10 were stale, losing v1.5.x fixes on deploy)
- **CRITICAL:** `hooks/pre-push` — Removed `set -e` that killed script before error handlers ran
- **CRITICAL:** `hooks/pre-commit` — Same `set -e` fix for scanner error handler
- **HIGH:** `load-qa-add.ps1` — Replaced hardcoded user path with `$MyInvocation.MyCommand.Definition`
- **HIGH:** `_dream_query*.py` — Replaced 6 hardcoded user paths with `os.path.expanduser()`
- **MEDIUM:** `bitbucket-pipelines.yml` — Fixed mypy target from gitignored `bitbucket-qa/` to `*.py`
- **MEDIUM:** `bitbucket-pipelines.yml` — Removed `|| true` from pylint step
- `performance_benchmark.py` — Fixed `name: str = None` → `Optional[str] = None`
- `pipeline_dashboard.py` — Fixed negative failed count in `simulate_pipeline_data()`
- `qa-add.ps1` — Improved filename escaping for `"` and backtick characters

### Changed
- Removed 8 unused packages from `requirements.txt`: click, numpy, pandas, tqdm, pyyaml, GitPython, typing-extensions, memory-profiler
- Removed 11 unused imports across 5 files

### Added
- `tests/__init__.py` — Created missing package init file

---

## [1.5.4] - 2026-07-21

### Fixed
- `setup.sh` — Fixed `cd "."` (no-op) → `cd "$(dirname "$0")"`
- `setup.sh` — Removed `2>/dev/null` that hid python3 errors
- `run-tests.bat` + `run-tests.sh` — Fixed venv path: `venv\` → `bitbucket-qa\venv\`
- `code_scanner.py` — Added `"bitbucket-qa"` to `EXCLUDE_DIRS`
- `hooks/pre-push` — Added `mkdir -p test-results` before pytest calls
- `run_full_pipeline.bat` — Removed `--exclude "bitbucket-qa"` from mypy and bandit
- `run_full_pipeline.sh` — Changed `2>/dev/null` → `2>&1` for bandit, radon, vulture, coverage

### Changed
- `smart_test_selector.py` — Hash now uses chunked reading (8KB chunks)
- `performance_benchmark.py` — Moved `example_function()` inside `if args.run_benchmarks` block

---

## [1.5.3] - 2026-07-21

### Fixed
- `qa-add.ps1` — Syntax check now uses `python -m py_compile` instead of PowerShell parser
- `qa-add.ps1` — Large file check now filters for code file extensions only
- `DEVELOPER_GUIDE.md` — Footer version updated from 1.5.0 to 1.5.2
- `run_full_pipeline.sh` — Tests step now uses `$QA_DIR/tests/` and `--cov="$QA_DIR"`

---

## [1.5.2] - 2026-07-21

### Fixed
- `test_precheck.py` — Removed broken `.git` walk-up logic
- `bitbucket-pipelines.yml` — CI now uses `test-matrix.json` for affected tests
- `smart_test_selector.py` — Fixed `_get_changed_lines()` to capture staged + unstaged changes
- `smart_test_selector.py` — Wired `_get_changed_functions()` into `get_affected_tests()`
- `smart_test_selector.py` — Auto-detect prefers tracked upstream branch
- `smart_test_selector.py` — `_get_merge_base()` no longer hardcodes `origin/`
- `run_full_pipeline.sh` — Changed `#!/bin/sh` to `#!/bin/bash`
- `setup_all.py` — Regenerated via `_gen_setup.py`
- Fixed path drift across README, QUICKSTART, EXECUTIVE_SUMMARY, PROJECT_OVERVIEW

---

## [1.5.1] - 2026-07-21

### Fixed
- `smart_test_selector.py` — Path separator duplication fixed (Windows `\` vs Linux `/`)
- `smart_test_selector.py` — Cache hash now includes source AND test files
- `smart_test_selector.py` — Git diff detects staged changes, untracked files, auto-detects base branch
- `test_phase1.sh` — Fixed Windows path check order

### Added
- `smart_test_selector.py` — `--base-branch` CLI argument
- `smart_test_selector.py` — `# test-depends:` comment-based dependency hints
- `smart_test_selector.py` — Weighted parallel grouping by execution time
- `smart_test_selector.py` — Line-level change granularity via `git diff --unified=0`

---

## [1.5.0] - 2026-07-20

### Fixed
- Added `code_scanner.py` to `setup_all.py` EMBEDDED_FILES
- Fixed `bitbucket-pipelines.yml` — removed undefined `${TESTS:-tests/}` variable
- Fixed `run_full_pipeline.sh` — removed `>/dev/null 2>&1` from lint commands
- `setup_all.py` — Python version parsing now uses regex
- `test_precheck.py` — Project root detection uses `.git` based logic
- `dependency_health.py` — Added `requests.Session` with `urllib3.Retry`
- `performance_benchmark.py` — Added `try-except` around `tracemalloc.start()`
- `pipeline_dashboard.py` — Added `timeout=10` to all `sqlite3.connect()` calls
- `smart_test_selector.py` — Added `SyntaxError` catch for AST parsing
- `setup_all.py` — Added `--force` flag, check before `run.bat` creation
- `run_full_pipeline.sh` — Replaced hardcoded paths with `QA_DIR` variable
- `dependency_health.py` — Changed PyUp 403 log from `debug` to `warning`
- `setup_all.py` — On Windows, installs `.bat` hooks instead of bash hooks
- Removed `--no-styles` flag from `hooks/pre-push`

### Added
- `DEVELOPER_GUIDE.md` — Complete 578-line guide

---

## [1.4.0] - 2026-07-16

### Added
- **`BRAIN.MD`** — Living operational journal. Auto-updated by MC after every meaningful change. Tracks decisions, fixes, architecture notes, and cross-session knowledge.
- **`hooks/pre-commit`** (Unix) — Fast pre-commit quality gate. Runs syntax check + code_scanner on staged Python files only (<5s). Blocks commit on errors.
- **`hooks/pre-commit.bat`** (Windows) — Same fast pre-commit gate for Windows developers.
- **`tests/test_quality_gate.py`** — 5 new pre-commit hook validation tests: exists, uses venv Python, runs scanner, checks staged files, blocks on errors.

### Changed
- **`setup_all.py` Step 6** — Now installs both pre-push AND pre-commit hooks. Updated banner to "Installing git hooks..."
- **`_gen_setup.py`** — Added `hooks/pre-commit` and `hooks/pre-commit.bat` to embedded files list.

### Hook Architecture
- **pre-commit** (fast gate): Syntax check + code_scanner on staged files only. Runs before every commit. Blocks on errors.
- **pre-push** (heavy gate): Code scanner + QA tests + coverage >= 30%. Runs before push. Blocks on errors.

---

## [1.3.0] - 2026-07-15

### Fixed

#### Critical (3)
- **`setup_all.py:176`** — Dead code after `return False` in `setup()` function. The `here = Path(...)` line was unreachable because it followed a `return` statement inside the `except ImportError` block. Removed the extra indentation to make it reachable.
- **`run_full_pipeline.bat:72-88`** — Double-nesting bug: scripts referenced `BitBucket QA\BitBucket QA\` instead of `BitBucket QA\`. Fixed all paths to use single nesting.
- **`bitbucket-pipelines.yml`** — Coverage threshold mismatch: CI enforced `--cov-fail-under=85` while the local pre-push hook used `--cov-fail-under=30`. Aligned CI to 30% to match the local hook.

#### Medium (7)
- **`dependency_health.py:102`** — Incomplete version specifier parser: only handled `==`, `>=`, `<=`. Added support for `~=`, `!=`, `>`, `<` operators.
- **`performance_benchmark.py:56-58`** — Dead code in benchmark decorator: `result = str(e)` was assigned before re-raising the exception, making it unreachable. Removed the dead assignment.
- **`performance_benchmark.py:334-347`** — `check_regressions()` returned `True` after finding the first regression, skipping remaining ones. Fixed to check all regressions and report all failures.
- **`pipeline_dashboard.py:109,179`** — SQLite connections not wrapped in `try/finally`. If an exception occurred between `connect()` and `close()`, the connection leaked. Added proper cleanup.
- **`smart_test_selector.py:147`** — Used `hashlib.md5()` for file content hashing. Replaced with `hashlib.sha256()` for better security practices.
- **`test_precheck.py`** — Did not exclude `BitBucket QA/` subdirectory or `_gen_setup.py` from syntax scanning. Added both to exclusion lists.
- **`_gen_setup.py:4`** — Contained hardcoded user-specific absolute path (`C:\Users\Akshaykumar Dudhwala\...`). Changed to use `Path(__file__).resolve().parent` for portability.

#### Low (5)
- **`test_phase1.sh`** — Missing `#!/bin/bash` shebang line. Added shebang.
- **`fix_encoding.sh`** — Missing `#!/bin/bash` shebang line. Added shebang.
- **`test_phase1.bat`** — Used `call venv\Scripts\activate` but venv is inside `BitBucket QA/venv/`. Fixed to use `BitBucket QA\venv\Scripts\python.exe`.
- **`test_phase1.sh`** — Used `source venv/bin/activate` but venv is inside `BitBucket QA/venv/`. Fixed to detect venv inside `BitBucket QA/`.
- **`bitbucket-pipelines.yml:101`** — Used `vulture --sort-by-size` which is not supported in vulture 2.x. Removed the flag.

### Changed
- **`bitbucket-pipelines.yml:48`** — Pylint step now redirects stderr to `/dev/null` for cleaner output while keeping `|| true` advisory behavior.
- **`bitbucket-pipelines.yml:57`** — Removed non-existent `mypy-report.txt` artifact reference (mypy outputs to stdout only).
- **`run_full_pipeline.sh:43`** — Removed unsupported `--sort-by-size` flag from vulture command.
- **`run_full_pipeline.bat`** — All pipeline output files (bandit, pip-audit, radon, vulture, test-results) now go inside `BitBucket QA/` instead of the project root.
- **`.gitignore`** — Cleaned up to properly exclude generated files including `.mypy_cache/` and `.test-cache/`.

### Added
- **`tests/test_quality_gate.py`** — 3 new isolation enforcement tests:
  - `test_pre_push_hook_delegates_to_qa_dir()` — Verifies hook `cd`s into `BitBucket QA/`
  - `test_no_hardcoded_user_paths()` — Catches hardcoded user paths like `C:\Users\...`
  - `test_setup_all_writes_only_to_qa_dir()` — Ensures setup targets only `BitBucket QA/`

### Security
- **Pre-push hook** — Completely rewritten to delegate all work to `BitBucket QA/`. The hook now `cd`s into the QA directory before running any checks, ensuring the developer's project files are never modified.
- **`hooks/pre-push.bat`** — Same isolation rewrite for Windows.

---

## [1.2.0] - 2026-07-10

### Fixed

#### Security (1)
- **`smart_test_selector.py`** — Bandit flagged `hashlib.md5()` as HIGH severity. Added `usedforsecurity=False` parameter.

#### Code Quality (317 lint issues resolved)
- All Python files — Auto-formatted with `black`, sorted imports with `isort`, fixed 317 flake8 issues.

### Changed
- **`bitbucket-pipelines.yml`** — Excluded submodule from mypy type checking.

### Added
- **`QUICKSTART.md`** — Quick start guide for new developers.

---

## [1.1.0] - 2026-06-29

### Fixed

#### Critical (4)
- **All 4 tools** — `base_dir` resolved to wrong directory. Changed to `Path(__file__).parent`.
- **`performance_benchmark.py`** — `--check-regressions` default was always truthy. Changed to `None` with guard.
- **`dependency_health.py`** — Version parsing included upper bounds. Added `.split(',')[0].strip()`.
- **`pipeline_dashboard.py`** — Orphaned rows on re-record. Now deletes child rows before inserting.

#### Medium (4)
- **`smart_test_selector.py`** — Missing existence check for `tests_dir`.
- **`performance_benchmark.py`** — `tracemalloc` restarts on every call. Added guard.
- **`dependency_health.py`** — PyUp API 403 errors silently failing. Added error handling.
- **`test_precheck.py`** — Test failures when CWD != project directory.

### Changed
- All 4 tools migrated from `print()` to `logging` module.
- `dependency_health.py` — Added pypistats cache with 24h TTL.
- HTML reports now use `html_module.escape()` for XSS prevention.

### Added
- **`tests/test_fixes.py`** — 13 unit tests for bug fixes.

---

## [1.0.0] - 2026-06-26

### Initial Release

#### Features
- Smart Test Selector, Performance Benchmark, Dependency Health Check, Pipeline Dashboard
- 6-stage BitBucket Pipeline with 11 steps
- Cross-platform setup scripts
- 28 Python dependencies with bounded version ranges
