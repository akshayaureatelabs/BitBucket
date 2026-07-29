# BRAIN.MD — BitBucket QA Project Journal

> Project-specific living journal. Updated by MC after every change to this project.
> For cross-project daily log, see `C:\Users\Akshaykumar Dudhwala\BKP\MC BRAIN\BRAIN.MD`

---

## Current State

- **Project**: BitBucket Pipeline QA & Utility Suite
- **Version**: v1.5.6
- **Last updated**: 2026-07-21
- **Author**: Sr. QA Tester — Akshaykumar Dudhwala
- **Active hooks**: pre-push.bat (heavy gate), pre-commit.bat (fast gate)
- **Test results**: 92 passed, 0 failed (code scanner: PASSED, setup: SUCCESS)

---

## Recent Changes (newest first)

### [2026-07-21] v1.5.6 — Post-Audit Fix (9 Issues)

**BUG FIXES (4):**
1. `run_full_pipeline.bat` — Added ERRORLEVEL checks to steps 4 (Security), 5 (Complexity), 7 (Benchmark), 9 (Dashboard) — they previously always reported PASS
2. `setup_all.py` — Added per-file skip logging ("SKIP: file (already exists, use --force)")
3. `tests/__init__.py` — Added comment to prevent empty-file scanner error (was causing setup failure)
4. `setup_all.py` — Added trailing newline (scanner flagged missing EOF newline)

**TEST IMPROVEMENTS (2):**
3. `test_quality_gate.py` — Added assertions to `test_pre_push_hook_exists`, `test_pre_commit_hook_exists`, `test_all_tools_importable` (were 0-assertion tests)
4. `tests/test_sample.py` — Refactored `test_imports` to parametrized pattern with explicit assertion (was `assert True` with unused imports)

**CLEANUP (2):**
5. `setup_all.py` — Converted CRLF to LF line endings (was only CRLF file in repo)
6. Removed stale `aureatelabs-bannerslider-hyva` submodule reference from git tracking

**DEPLOYMENT:**
- All 88 tests passed (up from 76 — no_bare_except and file_not_empty now scan deployed files too)
- Code scanner: PASSED (0 errors, 10 warnings — all false positives on test imports)
- `_gen_setup.py` regenerated embedded files

### [2026-07-21] v1.5.5 — 30-Pass Audit Fix (17 Issues)

**CRITICAL FIXES (4):**
1. `_gen_setup.py` — Added `code_scanner.py` to EMBEDDED_FILES sources (was missing — hooks couldn't find scanner on fresh deploy)
2. `setup_all.py` — Regenerated via `_gen_setup.py` to sync all 20 embedded files with latest source (10 were stale, losing all v1.5.x fixes on deploy)
3. `hooks/pre-push` — Removed `set -e` that killed script before error handlers ran; "PUSH BLOCKED" message was never printed
4. `hooks/pre-commit` — Same `set -e` fix; scanner error handler was dead code

**HIGH FIXES (2):**
5. `load-qa-add.ps1` — Replaced hardcoded `C:\Users\...` path with `$MyInvocation.MyCommand.Definition` for portability
6. `_dream_query.py` through `_dream_query6.py` — Replaced 6 hardcoded user paths with `os.path.expanduser(r"~\.local\...")`

**MEDIUM FIXES (2):**
7. `bitbucket-pipelines.yml` — Changed mypy target from `bitbucket-qa/` (gitignored, doesn't exist in CI) to `*.py`
8. `bitbucket-pipelines.yml` — Removed `|| true` from pylint step so lint failures are visible in CI

**TYPE SAFETY (1):**
9. `performance_benchmark.py` — Fixed `name: str = None` → `name: Optional[str] = None` (PEP 484)

**UNUSED IMPORTS (5):**
10. `dependency_health.py` — Removed unused `os`, `Any`
11. `performance_benchmark.py` — Removed unused `os`, `Any`, `List`
12. `pipeline_dashboard.py` — Removed unused `List`, `json`, `sys`, `px`
13. `_gen_setup.py` — Removed unused `re`
14. `_dream_query.py` — Removed unused `json`

**DEAD DEPENDENCIES (1):**
15. `requirements.txt` — Removed 8 unused packages: `click`, `numpy`, `pandas`, `tqdm`, `pyyaml`, `GitPython`, `typing-extensions`, `memory-profiler`

**BUG FIXES (2):**
16. `pipeline_dashboard.py` — Fixed `simulate_pipeline_data()` negative failed count with `max(0, ...)`
17. `qa-add.ps1` — Improved filename escaping to handle `"` and backtick characters

**NEW FILE:**
- `tests/__init__.py` — Created empty file (was missing on disk but referenced in EMBEDDED_FILES)

**DEPLOYMENT:**
- All 73 tests passed
- `_gen_setup.py` regenerated embedded files — all 20 files now match source

---

## Recent Changes (newest first)

### [2026-07-21] SESSION SUMMARY — Full Audit + 26 Fixes (v1.5.5 → v1.5.6)

**What happened today:**
Ran a comprehensive 30-pass forensic audit across all 58 source files. Found 30+ issues across critical, high, medium, and low severity. Fixed all verified issues in 3 rounds.

**Round 1 — v1.5.5 (17 fixes):**
- **CRITICAL:** Fixed `_gen_setup.py` missing `code_scanner.py` from embedded files (hooks couldn't find scanner on deploy)
- **CRITICAL:** Fixed `setup_all.py` stale embedded files (10 of 18 files were out of sync — all v1.5.x fixes lost on deploy)
- **CRITICAL:** Fixed `hooks/pre-push` and `hooks/pre-commit` — removed `set -e` that killed scripts before error handlers ran ("PUSH BLOCKED" was never printed)
- **HIGH:** Fixed hardcoded `C:\Users\...` paths in 7 files (`load-qa-add.ps1` + 6 `_dream_query*.py`)
- **MEDIUM:** Fixed `bitbucket-pipelines.yml` — mypy targeted gitignored dir, pylint swallowed failures with `|| true`
- **TYPE SAFETY:** Fixed `Optional[str]` in `performance_benchmark.py`
- **UNUSED IMPORTS:** Removed 11 unused imports across 5 files
- **DEAD DEPENDENCIES:** Removed 8 unused packages from `requirements.txt`
- **BUG FIXES:** Fixed negative failed count in `pipeline_dashboard.py`, improved escaping in `qa-add.ps1`

**Round 2 — v1.5.6 (9 fixes):**
- **BUG:** Fixed `run_full_pipeline.bat` — 4 steps (security, complexity, benchmark, dashboard) always reported PASS without error checking
- **BUG:** Fixed `tests/__init__.py` empty file causing setup failure (scanner treats empty as error)
- **BUG:** Added trailing newline to `setup_all.py` (scanner flagged missing EOF)
- **TESTS:** Added assertions to 3 zero-assertion tests in `test_quality_gate.py`
- **TESTS:** Refactored `test_sample.py` to parametrized import test with explicit assertion
- **CLEANUP:** Converted `setup_all.py` CRLF to LF, removed stale submodule reference

**Round 3 — Setup verification:**
- `python setup_all.py` — SUCCESS (92/92 tests passed, all 4 tools verified)
- Code scanner: PASSED (0 errors, 10 false-positive warnings on test imports)
- Pre-push + pre-commit hooks: installed and working

**Final state:**
- 92/92 tests pass
- Code scanner: PASSED
- 26 total fixes across v1.5.5 and v1.5.6
- All changes on disk, uncommitted (N-04)

---

### [2026-07-21] v1.5.4 — 10-Issue Fix

**BUG FIXES (7):**
1. `setup.sh` — Fixed `cd "."` (no-op) → `cd "$(dirname "$0")"`
2. `setup.sh` — Removed `2>/dev/null` that hid python3 errors
3. `run-tests.bat` + `run-tests.sh` — Fixed venv path: `venv\` → `bitbucket-qa\venv\`
4. `code_scanner.py` — Added `"bitbucket-qa"` to `EXCLUDE_DIRS`
5. `hooks/pre-push` — Added `mkdir -p test-results` before pytest calls
6. `run_full_pipeline.bat` — Removed `--exclude "bitbucket-qa"` from mypy and bandit (was cancelling target)
7. `run_full_pipeline.sh` — Changed `2>/dev/null` → `2>&1` for bandit, radon, vulture, coverage

**IMPROVEMENTS (2):**
8. `smart_test_selector.py` — Hash now uses chunked reading (8KB chunks) instead of loading full file
9. `performance_benchmark.py` — Moved `example_function()` inside `if args.run_benchmarks` block

**DEPLOYMENT:**
- 72/73 tests passed (1 expected failure: `_dream_query.py` external file)

### [2026-07-21] v1.5.3 — 4-Issue Polish Fix

**BUG FIXES (4):**
1. `qa-add.ps1` — Syntax check now uses `python -m py_compile` instead of PowerShell parser (was non-functional for Python)
2. `qa-add.ps1` — Large file check now filters for code file extensions only (was flagging binaries, .db, .zip)
3. `DEVELOPER_GUIDE.md` — Footer version updated from 1.5.0 to 1.5.2
4. `run_full_pipeline.sh` — Tests step now uses `$QA_DIR/tests/` and `--cov="$QA_DIR"` (was using bare `tests/` and `--cov=.`)

**DEPLOYMENT:**
- All 61 tests passed

### [2026-07-21] v1.5.2 — 9-Issue Code Review Fix

**BUG FIXES (6):**
1. `test_precheck.py` — Removed broken `.git` walk-up logic (was splitting path into components instead of walking parent dirs); kept correct fallback
2. `bitbucket-pipelines.yml` — CI now actually uses `test-matrix.json` to run only affected tests (was decorative — always ran full `tests/`)
3. `smart_test_selector.py` — `_get_changed_lines()` now uses `git diff HEAD --unified=0` to capture both staged + unstaged changes
4. `smart_test_selector.py` — `_get_changed_functions()` now wired into `get_affected_tests()` (was dead code)
5. `smart_test_selector.py` — Auto-detect now prefers tracked upstream branch (`HEAD@{upstream}`) before falling back to main/develop/master
6. `smart_test_selector.py` — `_get_merge_base()` no longer hardcodes `origin/` — tries branch name directly first, then falls back to `origin/`

**SCRIPT FIX (1):**
7. `run_full_pipeline.sh` — Changed `#!/bin/sh` to `#!/bin/bash` (script uses bash-isms)

**EMBEDDED FILES (1):**
8. `setup_all.py` — Regenerated via `_gen_setup.py` to include latest `dependency_health.py` with retry session

**DOCUMENTATION (1):**
9. Fixed "BitBucket QA/" → "bitbucket-qa/" path drift across README.md, QUICKSTART.md, EXECUTIVE_SUMMARY.md, PROJECT_OVERVIEW.md

**DEPLOYMENT:**
- All 61 tests passed
- `_gen_setup.py` regenerated embedded files

### [2026-07-21] v1.5.1 — Smart Test Selector 7-Fix + Code Review Cleanup

**CRITICAL FIXES (3):**
1. `smart_test_selector.py` — Path separator duplication fixed — all paths normalized to `Path(...).as_posix()` (was: `\` vs `/` caused same test in multiple parallel groups)
2. `smart_test_selector.py` — Cache hash now includes both source AND test files (was: only test files, so source changes were ignored)
3. `smart_test_selector.py` — git diff now detects staged changes (`--staged`), untracked files, AND auto-detects base branch diff

**MAJOR FIXES (1):**
4. `test_phase1.sh` — Fixed Windows path check order (was: checked `Scripts/python.exe` first on Linux; now checks `bin/python` first)

**ENHANCEMENTS (4):**
5. `smart_test_selector.py` — Added `--base-branch` CLI argument for manual base branch selection
6. `smart_test_selector.py` — Added `# test-depends:` comment-based dependency hints
7. `smart_test_selector.py` — Weighted parallel grouping by execution time (loads `.test-cache/timing.json`)
8. `smart_test_selector.py` — Added line-level change granularity via `git diff --unified=0` + AST function mapping

**DEPLOYMENT:**
- All 61 tests passed
- test-matrix.json: 4 unique tests (was 7 with 3 duplicates)

### [2026-07-20] v1.5.0 — 15 Issue Fix + Windows Hooks + Developer Guide

**CRITICAL FIXES (3):**
1. Added `code_scanner.py` to `setup_all.py` EMBEDDED_FILES (was missing — pre-push hook couldn't find it)
2. Fixed `bitbucket-pipelines.yml` — removed undefined `${TESTS:-tests/}` variable, replaced with direct `tests/`
3. Fixed `run_full_pipeline.sh` — removed `>/dev/null 2>&1` from lint commands, errors now visible

**MAJOR FIXES (6):**
4. `setup_all.py` — Python version parsing now uses regex (`re.search(r"Python (\d+)\.(\d+)")`) instead of fragile string split
5. `test_precheck.py` — Project root detection now uses `.git` based logic with walk-up fallback
6. `dependency_health.py` — Added `requests.Session` with `urllib3.Retry` (3 retries, backoff) for all API calls
7. `performance_benchmark.py` — Added `try-except` around `tracemalloc.start()` to handle memory limit failures
8. `pipeline_dashboard.py` — Added `timeout=10` to all `sqlite3.connect()` calls for concurrency safety
9. `smart_test_selector.py` — Added `SyntaxError` catch separate from generic `Exception` for AST parsing

**MINOR FIXES (4):**
10. `setup_all.py` — Added `--force` flag to overwrite existing QA files
11. `setup_all.py` — Added check before `run.bat` creation (won't overwrite without `--force`)
12. `run_full_pipeline.sh` — Replaced hardcoded `bitbucket-qa/` paths with `QA_DIR` variable
13. `dependency_health.py` — Changed PyUp 403 log from `debug` to `warning` with auth hint

**WINDOWS FIX (2):**
14. `setup_all.py` — On Windows, now installs `.bat` hooks instead of bash hooks (fixes "cannot spawn .git/hooks/pre-commit" error)
15. Removed `--no-styles` flag from `hooks/pre-push` (flag doesn't exist in `code_scanner.py`)

**DOCUMENTATION:**
- Created `DEVELOPER_GUIDE.md` — Complete 578-line guide covering setup, workflow, troubleshooting, FAQ

**DEPLOYMENT:**
- Successfully deployed to `aureatelabs-bannerslider-hyva` project
- All 94 tests passed on target project
- Pre-push + pre-commit hooks installed and working

### [2026-07-16] v1.4.0 — BRAIN.MD + Pre-commit + qa-add + Dev Runner

- Created `BRAIN.MD` as project living journal
- Created `hooks/pre-commit` (Unix) + `hooks/pre-commit.bat` (Windows)
  - Fast gate: syntax check + code_scanner on staged files only (<5s)
  - Blocks commit on errors
- Created `qa-add.ps1` — PowerShell function wrapping git add with 3 checks:
  1. Syntax check on .py files
  2. Code scanner (`code_scanner.py`)
  3. Large file check (>1MB)
- Created `load-qa-add.ps1` — profile loader for qa-add function
- Created `run-tests.bat` + `run-tests.sh` — independent test runner for devs
- Modified `setup_all.py` Step 6 — installs both pre-push + pre-commit hooks
- Modified `_gen_setup.py` — added pre-commit hooks to embedded files
- Added 5 pre-commit validation tests to `tests/test_quality_gate.py`
- Updated `CHANGELOG.md` (v1.4.0), `README.md`, `PROJECT_OVERVIEW.md`
- Fixed: BOM in 4 files, `--no-styles` flag removed from pre-commit hooks
- **Test results**: 56 passed, 5 skipped

### [2026-07-15] v1.3.0 — 35 Issue Fix

- 35 issues found and fixed: 1 CRITICAL, 7 HIGH, 13 MEDIUM, 14 LOW
- Critical: `setup_all.py` dead code, `run_full_pipeline.bat` double-nesting, CI coverage mismatch
- High: tz-aware/naive crashes, negative test counts, HTML malformation
- Medium: version parser, dead code, SQLite try/finally, MD5→SHA256, shebangs
- Coverage threshold standardized to 30%
- Folder renamed to `bitbucket-qa/` (lowercase)

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-21 | Remove `set -e` from hooks | `set -e` killed scripts before error handlers could run — dead code |
| 2026-07-21 | Add `code_scanner.py` to embedded files | Hooks call scanner but setup_all.py never deployed it |
| 2026-07-21 | Regenerate embedded files after every edit | 10/18 files were stale — v1.5.x fixes lost on deploy |
| 2026-07-21 | Use `os.path.expanduser()` for DB paths | Portable across users, no hardcoded home dirs |
| 2026-07-21 | Remove `|| true` from pylint in CI | Failures were invisible — defeats purpose of linting |
| 2026-07-21 | CI mypy targets `*.py` not `bitbucket-qa/` | `bitbucket-qa/` is gitignored, doesn't exist in CI |
| 2026-07-21 | Add ERRORLEVEL checks to all pipeline steps | 4/9 steps always reported PASS without checking |
| 2026-07-21 | Add comment to `tests/__init__.py` | Empty file causes scanner error, blocks setup |
| 2026-07-21 | Parametrize test imports | Better than `assert True` with unused imports |
| 2026-07-21 | Use git diff HEAD for line-level | Captures both staged and unstaged in one call |
| 2026-07-21 | Prefer upstream branch for base | Avoids picking wrong ancestor when feature is off develop not main |
| 2026-07-21 | Don't hardcode origin/ in merge-base | Teams may use upstream, bitbucket, or other remote names |
| 2026-07-21 | CI must use test-matrix.json | Matrix generation is useless if CI ignores it |
| 2026-07-21 | #!/bin/bash for scripts with bash-isms | #!/bin/sh fails on Debian/Ubuntu where /bin/sh is dash |
| 2026-07-21 | Normalize all paths to as_posix() | Windows `\` vs Linux `/` caused duplicate test entries |
| 2026-07-21 | Cache hashes source + test files | Source changes without test changes were being ignored |
| 2026-07-21 | Auto-detect base branch (main/develop/master) | Developers shouldn't need to manually specify base branch |
| 2026-07-21 | Comment-based test-depends hints | Dynamic imports and fixtures can't be detected by AST alone |
| 2026-07-20 | Windows uses .bat hooks | Bash hooks fail on Windows without sh.exe |
| 2026-07-20 | .gitignore update before tests | Test `test_gitignore_excludes_bitbucket_qa` was failing |
| 2026-07-20 | Remove --no-styles flag | Flag doesn't exist in code_scanner.py |
| 2026-07-20 | Add --force flag to setup_all.py | Allow overwriting existing QA files |
| 2026-07-20 | API retry with urllib3.Retry | Network failures shouldn't crash dependency health check |
| 2026-07-20 | SQLite timeout=10 | Prevent database lock on concurrent access |
| 2026-07-16 | Pre-commit = fast gate only | Syntax + scanner on staged files; heavy checks in pre-push |
| 2026-07-16 | BRAIN.MD = project-specific | Cross-project log lives in MC BRAIN |
| 2026-07-15 | Coverage threshold = 30% | Minimum viable; raise as test suite grows |
| 2026-07-15 | bitbucket-qa/ folder lowercase | User preference |
| 2026-07-15 | Script isolation principle | Never modify developer project files |
| 2026-07-15 | _gen_setup.py only replaces EMBEDDED_FILES | Anchor-based replacement is fragile |

---

## Known Issues / TODO

- Consider adding `.test-cache/timing.json` collection to CI pipeline for better weighted grouping
- Add `--changed-functions` CLI flag to surface function-level change info
- Add `.test-cache/timing.json` auto-collection to test runner scripts

---

## Architecture

### Hook Architecture (v1.5.0)

```
Windows:                              Linux/Mac:
pre-commit.bat (fast gate, <5s)      pre-commit (fast gate, <5s)
├─ Syntax check (staged .py)         ├─ Syntax check (staged .py)
├─ Code scanner (staged files)       ├─ Code scanner (staged files)
└─ Blocks on errors                  └─ Blocks on errors

pre-push.bat (heavy gate, 30-60s)    pre-push (heavy gate, 30-60s)
├─ 1/4: Code scanner (full repo)     ├─ 1/4: Code scanner (full repo)
├─ 2/4: QA unit tests (pytest)       ├─ 2/4: QA unit tests (pytest)
├─ 3/4: Coverage >= 30%              ├─ 3/4: Coverage >= 30%
└─ 4/4: Summary                      └─ 4/4: Summary
```

### Setup Flow (v1.5.0)

```
python setup_all.py [--force] [--skip-tests]
    │
    ├─ Step 1: Write QA files (base64 decode)
    ├─ Step 2: Check Python version (3.11+)
    ├─ Step 3: Create virtual environment
    ├─ Step 4: Install dependencies + Update .gitignore
    ├─ Step 5: Run validation tests
    └─ Step 6: Install git hooks (.bat on Windows, bash on Linux/Mac)
```

### Key Commands

```powershell
# Setup
python setup_all.py                    # One-click install (all files + hooks)
python setup_all.py --force            # Overwrite existing files
python setup_all.py --skip-tests       # Skip validation

# Testing
python -m pytest tests/ -v             # Run all tests
python code_scanner.py .               # Manual code scan
run.bat                                # Quick test runner
run_full_pipeline.bat                  # Full 9-step pipeline

# Tools
python dependency_health.py --check-all --generate-report
python performance_benchmark.py --run-benchmarks --generate-report
python pipeline_dashboard.py --record-metrics --generate-dashboard --days 30
python smart_test_selector.py --generate-matrix --summary
```

---

## Cross-Session Knowledge

- **vulture 2.x** dropped `--sort-by-size` flag — use `vulture . --min-confidence 80`
- **PowerShell** doesn't support `&&` and `||` — use semicolons or if/else
- **`.gitignore`** doesn't untrack already-committed files — must use `git rm --cached`
- **Pre-push/pre-commit hooks and embedded base64 must stay in sync** — after editing hooks, regenerate with `_gen_setup.py`
- **User prefers commands only for git operations** — "bhai tu sirf command bata me khud karunga vo"
- **Windows needs .bat hooks** — bash hooks fail with "cannot spawn" error
- **.gitignore must be committed before branch switch** — setup_all.py adds bitbucket-qa/ automatically
- **code_scanner.py has NO --no-styles flag** — don't use it in hooks
- **API calls need retry logic** — network failures crash dependency_health.py without urllib3.Retry
- **SQLite needs timeout** — concurrent access causes "database is locked" without timeout=10
- **Always use Path(...).as_posix()** — `str(Path(...))` returns `\` on Windows, `/` on Linux; causes duplicate keys in dicts
- **Cache must include source files** — hashing only test files misses source code changes
- **git diff needs --staged** — unstaged-only misses `git add`ed files
- **test_phase1.sh checks bin/python first** — .sh scripts run on Linux/Mac, not Windows
- **git diff HEAD captures both staged + unstaged** — single call instead of two
- **Never hardcode origin/ in git commands** — use branch name directly, git resolves tracking
- **Use upstream branch for base diff** — `git rev-parse --abbrev-ref HEAD@{upstream}` is more accurate than guessing main/develop
- **CI must use the matrix it generates** — decorative matrix wastes compute
- **#!/bin/bash not #!/bin/sh** — if script uses function keyword, [[, $(( )), etc.
- **Empty files cause scanner errors** — `tests/__init__.py` needs at least a comment
- **CRLF causes Unix git issues** — always use LF for cross-platform scripts
- **Stale submodule references linger** — use `git rm --cached` to remove orphaned entries
- **`set -e` + explicit error checking = dead code** — choose one or the other, not both
- **`|| true` in CI swallows real failures** — lint steps should fail the build
- **Test imports inside try/except are valid** — but scanner flags them as unused (false positive)
