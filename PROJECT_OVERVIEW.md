# BitBucket Pipeline QA & Utility Suite — Complete Project Overview

> **Version:** 1.0.0  
> **Last Updated:** June 26, 2026  
> **Status:** Production Ready  
> **Python:** 3.11+ (tested on 3.14.5)  
> **Platform:** Windows, Linux, macOS

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [Why Does It Exist?](#2-why-does-it-exist)
3. [Architecture Overview](#3-architecture-overview)
4. [Project Structure](#4-project-structure)
5. [How to Set Up (Developer Guide)](#5-how-to-set-up)
6. [Tools Deep Dive](#6-tools-deep-dive)
7. [CI/CD Pipeline Explained](#7-cicd-pipeline-explained)
8. [How the Pipeline Works (Stage by Stage)](#8-how-the-pipeline-works)
9. [Data Flow Diagram](#9-data-flow-diagram)
10. [Testing Strategy](#10-testing-strategy)
11. [Bugs Found & Fixed](#11-bugs-found--fixed)
12. [Dependencies & Versioning](#12-dependencies--versioning)
13. [Generated Files & Artifacts](#13-generated-files--artifacts)
14. [Troubleshooting](#14-troubleshooting)
15. [FAQ](#15-faq)

---

## 1. What Is This Project?

This is a **Python-based QA automation and CI/CD utility suite** for BitBucket Pipelines. It provides tools that:

- **Automatically select** which tests to run based on code changes (saves CI time)
- **Track performance** of code over time (detect regressions early)
- **Monitor dependency health** (find outdated or vulnerable packages)
- **Visualize pipeline metrics** in an interactive dashboard
- **Enforce code quality** via linting, type checking, and security scanning

Think of it as a **quality gate** — every code change passes through multiple automated checks before it can be merged.

---

## 2. Why Does It Exist?

Without this suite, a typical BitBucket Pipeline:
- Runs **all tests** every time (slow, wasteful)
- Has **no performance tracking** (regressions go unnoticed)
- Has **no dependency monitoring** (vulnerable packages stay forever)
- Has **no visual dashboard** (pipeline health is invisible)

**With this suite:**
- Only **affected tests** run (faster pipelines)
- Performance is **tracked and compared** against baselines
- Dependencies are **automatically checked** for vulnerabilities
- A **visual dashboard** shows pipeline health at a glance
- Code quality is **automatically enforced** on every PR

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    BitBucket Pipeline                         │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │  Smart   │   │  Lint &  │   │  Tests & │   │  Perf    │ │
│  │  Cache   │   │  Format  │   │ Coverage │   │ Benchmark│ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │  Pre-    │   │  Type    │   │ Security │   │  Dep     │ │
│  │  check   │   │  Check   │   │  Scan    │   │ Health   │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│  ┌──────────┐   ┌──────────┐                                │
│  │  Test    │   │ Complexity│                                │
│  │ Impact   │   │  Check    │                                │
│  └──────────┘   └──────────┘                                │
│                        │                                      │
│                        ▼                                      │
│              ┌──────────────────┐                            │
│              │    Pipeline      │                            │
│              │    Dashboard     │                            │
│              └──────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

**Key principle:** Everything runs inside the BitBucket Pipeline. Developers just push code — the pipeline handles quality checks automatically.

---

## 4. Project Structure

```
BitBucket/
│
├── bitbucket-pipelines.yml     # CI/CD pipeline configuration (11 steps)
├── requirements.txt            # 28 Python packages with version bounds (>=X,<Y)
│
├── setup_all.py                # Cross-platform setup script (Win/Linux/Mac)
├── setup.bat                   # Windows wrapper (calls setup_all.py)
├── setup.sh                    # Linux/macOS wrapper (calls setup_all.py)
│
├── smart_test_selector.py      # Test impact analysis tool
├── performance_benchmark.py    # Performance tracking & regression detection
├── dependency_health.py        # Dependency vulnerability & health checking
├── pipeline_dashboard.py       # Interactive pipeline metrics dashboard
│
├── test_precheck.py            # Pre-merge validation tests (5 test cases)
├── tests/
│   └── test_sample.py          # Sample test suite (2 test cases)
│
├── fix_encoding.bat            # Fix encoding issues (Windows)
├── fix_encoding.sh             # Fix encoding issues (Linux/macOS)
├── test_phase1.bat             # Quick test runner (Windows)
├── test_phase1.sh              # Quick test runner (Linux/macOS)
│
├── README.md                   # Team documentation
├── .gitignore                  # Git ignore rules
└── venv/                       # Virtual environment (not in git)
```

---

## 5. How to Set Up

### Option A: One-Click Setup (Recommended)

**Windows:**
```batch
setup.bat
```

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**What it does automatically:**
1. Checks Python version (needs 3.11+)
2. Creates virtual environment (`venv/`)
3. Installs all 28 dependencies
4. Runs 7 validation tests
5. Verifies all 4 tools import correctly
6. Shows available commands

### Option B: Manual Setup

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### Option C: No Local Setup Needed

The pipeline runs automatically on BitBucket. Just push code — no local setup required.

---

## 6. Tools Deep Dive

### 6.1 Smart Test Selector (`smart_test_selector.py`)

**Purpose:** Analyze code changes and run only the affected tests.

**How it works:**
1. Reads git diff to find changed files
2. Parses Python AST to map source files → test files
3. Generates a `test-matrix.json` with affected tests
4. Pipeline reads this matrix and skips unaffected tests

**Key class:** `SmartTestSelector`

**Key methods:**
- `_get_changed_files()` — Gets files changed via git diff (supports PR diffs and local diffs)
- `_build_test_mapping()` — Parses test files' imports using Python AST to create source→test mapping
- `get_affected_tests()` — Returns set of test files affected by changes
- `generate_test_matrix()` — Produces JSON matrix for parallel test execution
- `should_run_tests()` — Cache-based check using MD5 hashes to skip unchanged tests

**Intelligence features:**
- If `requirements.txt` changes → ALL tests run (dependency changes affect everything)
- If only a test file changes → only that test runs
- If a source file changes → tests that import it run
- MD5 caching prevents re-running identical tests

**CLI:**
```bash
python smart_test_selector.py --summary --generate-matrix
python smart_test_selector.py --generate-matrix --output my-matrix.json
```

---

### 6.2 Performance Benchmark (`performance_benchmark.py`)

**Purpose:** Track execution time, memory, and CPU to detect regressions.

**How it works:**
1. Decorates functions with `@benchmark.benchmark("name")`
2. Measures: execution time, CPU time, memory before/after, peak memory
3. Saves results to `.benchmarks/current.json`
4. Compares against saved baseline to find regressions

**Key class:** `PerformanceBenchmark`

**Key methods:**
- `benchmark(name)` — Decorator that instruments any function with timing/memory tracking
- `save_baseline()` — Saves current results as the baseline (also creates timestamped backup)
- `compare_with_baseline()` — Returns regressions (>10% slower) and improvements (>5% faster)
- `generate_html_report()` — Produces `.benchmarks/performance-report.html`
- `check_regressions(threshold)` — Returns True if any function exceeds threshold

**Measurement data per benchmark:**
```json
{
  "name": "example_function",
  "timestamp": "2026-06-26T16:00:00",
  "execution_time": 0.102,
  "cpu_time": 0.098,
  "memory_before_mb": 15.2,
  "memory_after_mb": 15.4,
  "memory_peak_mb": 0.3,
  "memory_increase_mb": 0.2,
  "cpu_percent": 2.1
}
```

**CLI:**
```bash
python performance_benchmark.py --run-benchmarks --generate-report
python performance_benchmark.py --save-baseline
python performance_benchmark.py --compare-baseline
python performance_benchmark.py --check-regressions 15.0
```

---

### 6.3 Dependency Health Check (`dependency_health.py`)

**Purpose:** Monitor all packages for outdated versions, vulnerabilities, and overall health.

**How it works:**
1. Parses `requirements.txt` to get all packages
2. Queries PyPI API for latest version and metadata
3. Queries OSV.dev and PyUp for known vulnerabilities
4. Calculates a health score (0-100) per package
5. Generates HTML report with recommendations

**Key class:** `DependencyHealthCheck`

**Health score factors:**
| Factor | Impact |
|--------|--------|
| No release in 365+ days | -20 points |
| No release in 180+ days | -10 points |
| Low downloads (<1000/month) | -15 points |
| Each vulnerability found | -10 points (max -50) |
| Project in Planning/Pre-Alpha | -25 to -30 points |
| Project in Alpha | -15 points |
| Project in Beta | -5 points |
| Mature project | +5 points |
| Inactive project | -40 points |

**Data sources:**
- **PyPI API** — Package metadata, release history, download stats
- **OSV.dev** — Open Source Vulnerability database
- **PyUp** — Additional vulnerability data
- **pypistats.org** — Download statistics

**Caching:** Results cached for 24 hours (PyPI) and 6 hours (vulnerabilities)

**CLI:**
```bash
python dependency_health.py --check-all --generate-report
python dependency_health.py --check-all --fail-on-issues
python dependency_health.py --check-all --output-json report.json
```

---

### 6.4 Pipeline Dashboard (`pipeline_dashboard.py`)

**Purpose:** Record pipeline metrics and generate interactive visual dashboard.

**How it works:**
1. Records each pipeline run to SQLite database
2. Collects: run status, duration, branch, test results, step metrics
3. Generates Plotly-based interactive HTML dashboard

**Key class:** `PipelineDashboard`

**Database schema:**
```
pipeline_runs (run_id, timestamp, branch, commit_hash, status, duration, ...)
step_metrics (run_id, step_name, duration, status, ...)
test_results (run_id, total_tests, passed, failed, coverage, ...)
performance_metrics (run_id, function_name, execution_time, memory_used, ...)
```

**Dashboard charts:**
1. Daily Pipeline Runs (bar chart)
2. Success Rate by Branch (bar chart with color coding)
3. Step Duration (bar chart — which steps are slowest)
4. Test Coverage Trend (line chart with 85% minimum line)
5. Pipeline Duration Trend (line chart)
6. Step Success Rate (bar chart)

**BitBucket environment variables used:**
- `BITBUCKET_BUILD_NUMBER`, `BITBUCKET_BRANCH`, `BITBUCKET_COMMIT`
- `BITBUCKET_COMMIT_MESSAGE`, `BITBUCKET_PR_ID`, `BITBUCKET_EXIT_CODE`

**CLI:**
```bash
python pipeline_dashboard.py --record-metrics
python pipeline_dashboard.py --generate-dashboard --days 30
python pipeline_dashboard.py --simulate-data  # Generate test data
```

---

## 7. CI/CD Pipeline Explained

### Pipeline Configuration (`bitbucket-pipelines.yml`)

**Image:** `python:3.11`  
**Docker:** Enabled  
**Size:** 2x (double resources)  
**Max timeout:** 30 minutes per step  
**Caches:** pip packages + pytest cache (persisted between runs)

### Trigger Types

| Trigger | When | Stages Run |
|---------|------|-----------|
| Pull Request | Any PR | Full pipeline (all 6 stages) |
| Push to `main` | Merge to main | Full pipeline (all 6 stages) |
| Push to other branch | Any feature branch | Quick validation only (stages 1, 3, 4) |

---

## 8. How the Pipeline Works (Stage by Stage)

### Stage 1: Cache & Precheck (Parallel)

**Step 1a — Smart Cache Setup:**
```
pip install --upgrade pip
pip install -r requirements.txt
pip freeze > installed-packages.txt
```
- Installs all dependencies
- Saves frozen package list as artifact

**Step 1b — Pre-merge Validation:**
```
pytest test_precheck.py -v --junitxml=test-results/precheck.xml
```
- Validates Python syntax of all `.py` files
- Checks no empty files exist
- Verifies `requirements.txt` and `bitbucket-pipelines.yml` exist
- Produces JUnit XML for BitBucket UI

### Stage 2: Test Impact Analysis

```
python smart_test_selector.py --generate-matrix --summary
```
- Analyzes git diff to find changed files
- Maps changes to affected tests
- Outputs `test-matrix.json` used by later stages
- If no tests affected → runs smoke tests or all tests

### Stage 3: Quality Checks (Parallel)

**Step 3a — Lint & Format:**
```
black --check . --diff          # Code formatting
isort --check-only . --diff    # Import sorting
flake8 . --max-line-length=120 # Style guide
pylint **/*.py --fail-under=8.0 || true  # Code analysis (advisory)
```

**Step 3b — Type Checking:**
```
mypy . --ignore-missing-imports --strict
```
- Static type analysis
- Strict mode with import ignore

**Step 3c — Security Scan:**
```
bandit -r . -ll -f json -o bandit-report.json
pip-audit --requirement requirements.txt -f json -o pip-audit.json
```
- **bandit** — Finds common security issues in Python code
- **pip-audit** — Checks packages against vulnerability databases

**Step 3d — Complexity & Dead Code:**
```
radon cc . -s -n B --json > radon-report.json
vulture . --min-confidence 80 --sort-by-size > vulture-report.txt
```
- **radon** — Cyclomatic complexity analysis (flags grade B and below)
- **vulture** — Finds unused code (80% confidence threshold)

### Stage 4: Tests & Coverage

```
pytest tests/ -n auto --dist loadscope \
  --cov=. --cov-report=xml --cov-report=html \
  --cov-fail-under=85 \
  --junitxml=test-results/results.xml \
  --html=test-results/report.html --self-contained-html
```
- Runs affected tests (from test-matrix.json) or all tests
- Parallel execution with `pytest-xdist` (`-n auto`)
- Coverage minimum: **85%** (pipeline fails if below)
- Produces: XML report, HTML report, coverage XML

### Stage 5: Benchmark & Dependencies (Parallel)

**Step 5a — Performance Benchmark:**
```
python performance_benchmark.py --run-benchmarks --generate-report
python performance_benchmark.py --compare-baseline
```
- Runs benchmarks and compares against baseline
- Flags regressions >10%

**Step 5b — Dependency Health:**
```
python dependency_health.py --check-all --generate-report --fail-on-issues
```
- Checks all 28 packages for vulnerabilities and updates
- Fails pipeline if critical issues found

### Stage 6: Dashboard

```
python pipeline_dashboard.py --record-metrics
python pipeline_dashboard.py --generate-dashboard --days 30
```
- Records this run's metrics to SQLite database
- Regenerates the interactive dashboard
- Dashboard HTML saved as artifact

---

## 9. Data Flow Diagram

```
Developer Push
      │
      ▼
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│  git diff    │────▶│ Smart Test      │────▶│ test-matrix  │
│  analysis    │     │ Selector        │     │ .json        │
└─────────────┘     └─────────────────┘     └──────┬───────┘
                                                    │
      ┌─────────────────────────────────────────────┘
      │
      ▼
┌─────────────┐     ┌─────────────────┐
│ pytest with │────▶│ Coverage XML/HTML│
│ -n auto     │     │ + JUnit XML     │
└─────────────┘     └─────────────────┘

┌─────────────┐     ┌─────────────────┐
│ PyPI + OSV  │────▶│ Health Report   │
│ API queries │     │ (HTML)          │
└─────────────┘     └─────────────────┘

┌─────────────┐     ┌─────────────────┐
│ Benchmark   │────▶│ performance-    │
│ execution   │     │ report.html     │
└─────────────┘     └─────────────────┘

┌─────────────┐     ┌─────────────────┐
│ Metrics DB  │────▶│ Dashboard HTML  │
│ (SQLite)    │     │ (Plotly charts) │
└─────────────┘     └─────────────────┘
```

---

## 10. Testing Strategy

### Test Layers

| Layer | File | Tests | Purpose |
|-------|------|-------|---------|
| **Precheck** | `test_precheck.py` | 5 | Syntax validation, file existence |
| **Sample** | `tests/test_sample.py` | 2 | Import validation, basic sanity |
| **Integration** | Pipeline stages | All | End-to-end pipeline validation |
| **Manual** | setup_all.py | 4 tool checks | Verify all tools import correctly |

### Precheck Tests (Detailed)

1. **test_python_syntax** — Parses every `.py` file with `ast.parse()` to catch syntax errors
2. **test_no_empty_python_files** — Checks file sizes aren't zero
3. **test_requirements_exists** — Confirms `requirements.txt` is present
4. **test_pipeline_yml_exists** — Confirms `bitbucket-pipelines.yml` is present

### Test Execution Flow

```
PR Created
    │
    ▼
Stage 1: Precheck (5 tests, fast)
    │
    ▼
Stage 2: Test Impact Analysis → test-matrix.json
    │
    ▼
Stage 4: Run affected tests (parallel, with coverage)
    │
    ▼
Coverage >= 85%? ──── NO ──── Pipeline FAILS
    │
   YES
    │
    ▼
Pipeline PASSES ✓
```

---

## 11. Bugs Found & Fixed

### Bugs Fixed During Development

| # | File | Bug | Fix | Severity |
|---|------|-----|-----|----------|
| 1 | `requirements.txt` | Pinned `==` versions incompatible with Python 3.14 | Changed to `>=X,<Y` upper bounds | Critical |
| 2 | `performance_benchmark.py` | `%` in argparse help string crashes on Python 3.14 | Changed to "threshold percent" | Medium |
| 3 | `pipeline_dashboard.py` | `GROUP BY date` / `ORDER BY date` SQLite alias conflicts with built-in `date()` function | Changed to `GROUP BY DATE(timestamp) ORDER BY DATE(timestamp)` | Critical |
| 4 | `setup.bat` | Duplicate `if %errorlevel%` lines after edit | Replaced with thin wrapper calling `setup_all.py` | Low |
| 5 | `setup.sh` | CRLF line endings break on Linux/macOS | Converted to LF, rewrote as thin wrapper | Medium |
| 6 | `setup_all.py` | `shell=True` with list + paths containing spaces breaks on Windows | Removed `shell=True`, use list directly | Critical |
| 7 | `setup_all.py` | Direct `pip.exe` call fails when pip module missing | Changed to `python -m pip` with ensurepip fallback | Medium |

### Root Cause of Bug #1
Old venv was created with Python 3.10 but system has Python 3.14. The pinned versions (`pandas==2.0.3`, `numpy==1.24.3`) use C extensions that fail to compile on Python 3.14 because `pkg_resources` was removed.

### Root Cause of Bug #3
SQLite treats `date` as a function name. When a column alias is named `date`, `GROUP BY date` calls the `date()` function instead of grouping by the column.

---

## 12. Dependencies & Versioning

### Version Strategy
All packages use **bounded ranges** (`>=X,<Y`):
- **Lower bound:** Minimum version that works
- **Upper bound:** Next major version (prevents breaking changes)

This balances:
- **Flexibility** — Patch/minor updates allowed
- **Stability** — No surprise major version breaks
- **Security** — Vulnerability fixes applied automatically

### Package List (28 packages)

| Category | Packages |
|----------|----------|
| **Testing** | pytest, pytest-cov, pytest-xdist, pytest-html, pytest-timeout, pytest-mock |
| **Code Quality** | black, isort, flake8, mypy, pylint, radon, vulture |
| **Security** | bandit, pip-audit |
| **Performance** | psutil, memory-profiler |
| **Data** | pandas, numpy, plotly |
| **Git** | GitPython |
| **Utilities** | requests, python-dateutil, typing-extensions, click, colorama, tqdm, pyyaml |

### Installation Notes
- Python 3.14 removed `pkg_resources` (used by older pandas/numpy)
- `setuptools` package may need manual install on Python 3.14
- All packages tested working with `>=` pins on Python 3.14.5

---

## 13. Generated Files & Artifacts

### Files Created by Tools

| File | Created By | Purpose |
|------|-----------|---------|
| `test-matrix.json` | smart_test_selector | List of tests to run |
| `.test-cache/last_test_hash.txt` | smart_test_selector | MD5 cache for test change detection |
| `.benchmarks/current.json` | performance_benchmark | Latest benchmark results |
| `.benchmarks/baseline.json` | performance_benchmark | Saved baseline for comparison |
| `.benchmarks/performance-report.html` | performance_benchmark | HTML report with charts |
| `dependency-reports/latest_report.html` | dependency_health | Latest health report |
| `dependency-reports/pypi_cache.json` | dependency_health | Cached PyPI data (24h) |
| `dependency-reports/vuln_cache.json` | dependency_health | Cached vulnerability data (6h) |
| `pipeline-metrics.db` | pipeline_dashboard | SQLite database with run history |
| `dashboard/dashboard.html` | pipeline_dashboard | Interactive Plotly dashboard |
| `installed-packages.txt` | Pipeline | pip freeze output |
| `test-results/precheck.xml` | Pipeline | JUnit test results |
| `test-results/results.xml` | Pipeline | JUnit test results |
| `test-results/report.html` | Pipeline | HTML test report |
| `coverage.xml` | Pipeline | Coverage data (Cobertura format) |
| `htmlcov/**` | Pipeline | Coverage HTML report |
| `bandit-report.json` | Pipeline | Security scan results |
| `pip-audit.json` | Pipeline | Dependency audit results |
| `radon-report.json` | Pipeline | Code complexity data |
| `vulture-report.txt` | Pipeline | Dead code analysis |

### Git-Ignored Files
All generated files are excluded from git via `.gitignore`:
- `*.db`, `dashboard/`, `.benchmarks/`, `dependency-reports/`
- `.pytest_cache/`, `__pycache__/`, `venv/`
- `coverage.xml`, `htmlcov/`, `test-results/`
- `*.html` (except `index.html`), `installed-packages.txt`

---

## 14. Troubleshooting

### Common Issues

**"Python not found"**
- Install Python 3.11+ from https://www.python.org/downloads/
- On Windows, check "Add Python to PATH" during installation

**"No module named pip" in venv**
- Run: `python -m ensurepip --upgrade`
- Or delete `venv/` and run `setup.bat` / `setup.sh` again

**"PermissionError: [WinError 5]" when deleting venv**
- Close all Python processes, IDE terminals, and command prompts
- Try running setup again

**"No module named pkg_resources" on Python 3.14**
- Run: `pip install setuptools`
- Then re-run setup

**Pipeline fails at coverage check (85% threshold)**
- Add tests for new code
- Check locally: `pytest tests/ --cov=. --cov-report=html`

**SQLite "ambiguous column: date" error**
- This was fixed — ensure you're using the latest code from `main`

**Encoding issues between Windows/Linux**
- Run: `fix_encoding.bat` (Windows) or `fix_encoding.sh` (Linux)

### Getting Help

1. Check this document first
2. Run `setup.bat` / `setup.sh` to verify environment
3. Run `pytest test_precheck.py -v` to validate project structure
4. Check pipeline logs on BitBucket for CI-specific issues

---

## 15. FAQ

**Q: Do I need to install this on my machine?**
A: No. The pipeline runs automatically on BitBucket. Local setup is optional for running tools manually.

**Q: What happens if I don't have Python 3.11+?**
A: The setup script will tell you to install it. The pipeline uses `python:3.11` Docker image so it always works in CI.

**Q: Can I run individual tools without the full pipeline?**
A: Yes. Each tool has its own CLI. See the Tools Deep Dive section above.

**Q: What if I break the pipeline?**
A: The pipeline is designed to catch issues before they reach `main`. Fix the issue in your PR and push again.

**Q: How do I add new tests?**
A: Add `test_*.py` files in the `tests/` directory. The smart test selector will automatically discover and map them.

**Q: How do I update dependencies?**
A: Edit `requirements.txt` with the new version bounds. The dependency health tool will validate them.

**Q: What does the dashboard show?**
A: Pipeline success rates, test coverage trends, step durations, and branch health — all from the last 30 days.

---

*Document generated as part of the BitBucket Pipeline QA & Utility Suite.*
*For questions, contact the team or check the README.md.*
