# BitBucket Pipeline QA & Utility Suite

A collection of Python-based tools and configurations that validate every code change **locally** before it is pushed. The project acts as a **quality gate** — nothing is pushed unless the local checks pass. (BitBucket Pipelines CI is supported but **not required**; the local pre-push hook is the primary gate.)

---

## Core Design Principle: Complete Isolation

**The entire QA suite lives inside the `bitbucket-qa/` folder and NEVER modifies, overwrites, or touches any existing file in the developer's project.**

- All tools, tests, virtual environment, and generated artifacts stay inside `bitbucket-qa/`
- The pre-push hook delegates to `bitbucket-qa/` — it never runs checks in the project root
- If the developer has `node_modules`, `.gitignore`, `package.json`, `.env`, `dist/`, or any other files, the QA suite will not touch them
- The only things outside `bitbucket-qa/` are `.git/hooks/pre-push` and `.git/hooks/pre-commit` (which Git requires there), and they simply `cd` into `bitbucket-qa/` before running anything

---

## Quick Reference

### First Time Setup
```bash
git clone <repo-url>
cd <repo-folder>
python setup_all.py
```
*Run this once — it will automatically create `bitbucket-qa/` with a virtual environment, install all packages, and run the validation suite.*

### Daily Workflow
```bash
git add -A
git commit -m "your message"   # pre-commit hook runs automatically (syntax + scanner)
git push                        # pre-push hook runs automatically (tests + coverage)
```
**Two-layer quality gate:**
- **On commit** (`pre-commit`): Fast check — syntax validation + code scanner on staged files only. Catches mistakes early.
- **On push** (`pre-push`): Heavy check — full code scanner + QA tests + coverage >= 30%. Final quality gate.
- *If **checks pass** → commit/push proceeds.*
- *If **any check fails** → commit/push is **blocked** and you must fix it first.*

### If Commit Is Blocked (pre-commit)
```bash
# Fix the syntax errors or scanner issues, then re-add and commit
git add -A
git commit -m "your message"
```

### If Push Is Blocked (pre-push)
```bash
# First, fix the errors
cd "bitbucket-qa"
python -m pytest test_precheck.py -v   # syntax / structure check
python -m pytest tests/ -v             # full test suite
python -m pytest tests/ --cov=. --cov-report=html   # see coverage in htmlcov/

# Then try pushing again
git push
```

### Extra Commands
```bash
cd "bitbucket-qa"
python dependency_health.py --check-all --generate-report    # Dependency health check
python pipeline_dashboard.py --simulate-data                # Dashboard generate
python performance_benchmark.py --run-benchmarks            # Performance benchmark
python smart_test_selector.py --summary --generate-matrix   # Test impact analysis
```

---

## Overview

This project provides a suite of utilities to enhance the development lifecycle:

- **Smart Test Selection** — Analyze code changes to run only relevant tests
- **Performance Benchmarking** — Track and compare execution metrics over time
- **Dependency Health** — Monitor and report on the status of project dependencies
- **Pipeline Dashboard** — Generate interactive visual reports of pipeline performance
- **Security & Quality** — Integrated linting, type checking, and security scanning

---

## Quick Start

### Prerequisites

- **Python 3.11+** (tested on 3.14.5; works on 3.11–3.14)
- `pip` (comes with Python)
- `git`

### One-Click Setup

#### Windows
```batch
setup.bat
```

#### Linux / macOS
```bash
chmod +x setup.sh
./setup.sh
```

The setup script (`setup_all.py`) will:
1. Create the `bitbucket-qa/` directory
2. Create a virtual environment inside it (`bitbucket-qa/venv/`)
3. Install all dependencies from `requirements.txt`
4. Run the validation suite
5. Verify all 4 tools import correctly

### Manual Setup

```bash
mkdir -p "bitbucket-qa"
cd "bitbucket-qa"
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r ../requirements.txt
```

---

## Local Quality Gate (Pre-Push Hook)

The `.git/hooks/pre-push` hook is the **primary quality gate**. It runs on every `git push`. The hook delegates all work to `bitbucket-qa/` — it never runs checks in the project root.

| Step | Check | Gate |
|------|-------|------|
| 1/3 | Tests (`pytest test_precheck.py tests/`) | **Blocking** |
| 2/3 | Coverage (`--cov-fail-under=30`) | **Blocking** |
| 3/3 | Lint & format (`black`, `isort`, `flake8`) | Advisory |

- **Tests and coverage block the push.** Lint prints warnings but does **not** block.
- The test count is **dynamic** — grows as you add `.py` files and tests.
- **Raise `--cov-fail-under`** (currently 30%) as coverage improves.
- For a full local run (all 9 checks), use `run_full_pipeline.bat` (Windows) / `run_full_pipeline.sh` (Linux).

---

## Tools

All tools are run from inside `bitbucket-qa/` using the venv Python.

### 1. Smart Test Selector (`smart_test_selector.py`)

Analyzes code changes (via `git diff`) to determine which tests are affected, then generates a test matrix for targeted runs.

```bash
cd "bitbucket-qa"
python smart_test_selector.py --summary --generate-matrix
python smart_test_selector.py --generate-matrix --output my-matrix.json
```

| Flag | Description |
|------|-------------|
| `--generate-matrix` | Generate `test-matrix.json` with affected test files |
| `--summary` | Print analysis summary to console |
| `-o, --output` | Output file path (default: `test-matrix.json`) |

---

### 2. Performance Benchmark (`performance_benchmark.py`)

Tracks execution time, memory usage, and CPU consumption. Compares against a saved baseline to detect regressions.

```bash
cd "bitbucket-qa"
python performance_benchmark.py --run-benchmarks --generate-report
python performance_benchmark.py --run-benchmarks --save-baseline
python performance_benchmark.py --compare-baseline
python performance_benchmark.py --check-regressions 15.0
```

| Flag | Description |
|------|-------------|
| `--run-benchmarks` | Execute benchmark suite |
| `--compare-baseline` | Compare current results with saved baseline |
| `--save-baseline` | Save current results as the new baseline |
| `--generate-report` | Generate HTML report |
| `--check-regressions` | Check if any function regressed beyond threshold (%) |

---

### 3. Dependency Health Check (`dependency_health.py`)

Checks for outdated packages, known vulnerabilities (via OSV.dev / PyUp), and overall dependency health.

```bash
cd "bitbucket-qa"
python dependency_health.py --check-all --generate-report
python dependency_health.py --check-all --fail-on-issues
python dependency_health.py --check-all --output-json report.json
```

| Flag | Description |
|------|-------------|
| `--check-all` | Run all dependency checks |
| `--generate-report` | Generate HTML report |
| `--fail-on-issues` | Exit with non-zero code if issues found |
| `--output-json` | Export results to a JSON file |

---

### 4. Pipeline Dashboard (`pipeline_dashboard.py`)

Records pipeline run metrics to a SQLite database and generates an interactive Plotly-based HTML dashboard.

```bash
cd "bitbucket-qa"
python pipeline_dashboard.py --record-metrics
python pipeline_dashboard.py --generate-dashboard --days 30
python pipeline_dashboard.py --simulate-data
```

| Flag | Description |
|------|-------------|
| `--record-metrics` | Record current pipeline run to database |
| `--generate-dashboard` | Generate interactive HTML dashboard |
| `--simulate-data` | Insert 100 sample pipeline runs for testing |
| `--days` | Number of days to include (default: 30) |

---

## Testing

All tests run from inside `bitbucket-qa/`:

```bash
cd "bitbucket-qa"
pytest test_precheck.py tests/ -v
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
pytest tests/ -n auto
```

### Test Coverage

| Test | Description |
|------|-------------|
| `test_python_syntax` | **Parametrized** — one test per `.py` file (validates syntax). Count grows with the codebase. |
| `test_no_empty_python_files` | Ensures no empty Python files exist |
| `test_requirements_exists` | Checks `requirements.txt` exists |
| `test_pipeline_yml_exists` | Checks `bitbucket-pipelines.yml` exists |
| `TestStripExtras` | 6 tests for extras parsing |
| `TestPypistatsCaching` | 4 tests for pypistats API cache |
| `TestTracemallocGuard` | 3 tests for tracemalloc guard |
| `test_pre_push_hook_delegates_to_qa_dir` | Verifies hook delegates to `bitbucket-qa/` |
| `test_no_hardcoded_user_paths` | Ensures no hardcoded user paths in source |
| `test_setup_all_writes_only_to_qa_dir` | Ensures setup targets only `bitbucket-qa/` |

---

## Optional: BitBucket Pipelines CI

`bitbucket-pipelines.yml` is provided as a **reference CI configuration**. The local pre-push hook is the primary gate.

### Pipeline Stages (if enabled)

```
Stage 1 (Parallel)  ──┬── Smart Cache Setup
                       └── Pre-merge Validation

Stage 2              ── Test Impact Analysis

Stage 3 (Parallel)  ──┬── Lint & Format
                       ├── Type Checking
                       ├── Security Scan
                       └── Complexity & Dead Code

Stage 4              ── Tests & Coverage

Stage 5 (Parallel)  ──┬── Performance Benchmark
                       └── Dependency Health

Stage 6              ── Pipeline Dashboard
```

### Coverage Threshold Consistency

The coverage threshold is **30%** everywhere — both the local pre-push hook and the CI pipeline use the same value.

---

## Project Structure

```
BitBucket/                         (project root)
├── bitbucket-pipelines.yml    # Optional CI reference config
├── requirements.txt           # Python dependencies
├── setup_all.py               # Creates bitbucket-qa/ with everything
├── setup.bat                  # One-click setup (Windows)
├── setup.sh                   # One-click setup (Linux/macOS)
├── run_full_pipeline.bat      # Full QA runner (Windows)
├── run_full_pipeline.sh       # Full QA runner (Linux)
├── test_precheck.py           # Pre-merge validation tests
├── tests/
│   ├── test_sample.py         # Sample tests
│   ├── test_fixes.py          # Unit tests for bug fixes
│   ├── test_quality_gate.py   # Quality gate enforcement tests
│   └── test_tools_units.py    # Unit tests for tool internals
├── smart_test_selector.py     # Test impact analysis tool
├── performance_benchmark.py   # Performance tracking utility
├── dependency_health.py       # Dependency health checker
├── pipeline_dashboard.py      # Pipeline metrics & dashboard
├── fix_encoding.bat           # Fix encoding issues (Windows)
├── fix_encoding.sh            # Fix encoding issues (Linux)
├── test_phase1.bat            # Phase 1 test runner (Windows)
├── test_phase1.sh             # Phase 1 test runner (Linux)
├── .git/hooks/pre-push        # LOCAL quality gate (delegates to bitbucket-qa/)
├── .gitignore                 # Git ignore rules
├── CHANGELOG.md               # Version history
├── QUICKSTART.md              # Quick start guide
├── PROJECT_OVERVIEW.md        # Full technical documentation
├── EXECUTIVE_SUMMARY.md       # Executive summary
└── README.md                  # This file
```

---

## Troubleshooting

### Push Blocked on Tests
- Read the failure output — it names the failing test
- Run locally: `cd "bitbucket-qa" && pytest test_precheck.py tests/ -v`
- Fix the code, commit, then `git push` again

### Push Blocked on Coverage
- Add tests for new code
- Check coverage locally: `cd "bitbucket-qa" && pytest tests/ --cov=. --cov-report=html`
- Raise the bar over time by increasing `--cov-fail-under` in the hook

### Hook Uses the Wrong Python
- Run `python setup_all.py` to (re)create the venv inside `bitbucket-qa/`

### Developer Files Modified by Script
**This should never happen.** The QA suite is completely isolated inside `bitbucket-qa/`. If any script modifies files outside that directory, it is a bug — report it immediately.

---

## Dependencies

All dependencies use bounded version ranges (`>=X,<Y`) for compatibility and stability.

Key dependencies: pytest, black, flake8, mypy, bandit, pip-audit, pandas, plotly, GitPython, psutil.

---

## Contributing

**Author:** Sr. QA Tester - Akshaykumar Dudhwala

1. Create a feature branch from `main`
2. Make your changes (inside `bitbucket-qa/` for QA tool changes)
3. Run locally: `cd "bitbucket-qa" && pytest test_precheck.py tests/ -v`
4. `git push` — the **local pre-push hook** automatically validates
5. Create a pull request

**Important:** Never modify files outside `bitbucket-qa/` from within the QA scripts. The developer's project files must remain untouched.
