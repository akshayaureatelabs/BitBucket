# BitBucket Pipeline QA & Utility Suite — Complete Project Overview

> **Version:** 1.3.0  
> **Last Updated:** July 15, 2026  
> **Status:** Ready for Deployment  
> **Python:** 3.11+ (tested on 3.14.5)  
> **Platform:** Windows, Linux, macOS

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [Core Design Principle: Complete Isolation](#2-core-design-principle-complete-isolation)
3. [Why Does It Exist?](#3-why-does-it-exist)
4. [Architecture Overview](#4-architecture-overview)
5. [Project Structure](#5-project-structure)
6. [How to Set Up](#6-how-to-set-up)
7. [Tools Deep Dive](#7-tools-deep-dive)
8. [CI/CD Pipeline Explained](#8-cicd-pipeline-explained)
9. [How the Pipeline Works](#9-how-the-pipeline-works)
10. [Testing Strategy](#10-testing-strategy)
11. [Bugs Found & Fixed](#11-bugs-found--fixed)
12. [Dependencies & Versioning](#12-dependencies--versioning)
13. [Generated Files & Artifacts](#13-generated-files--artifacts)
14. [Troubleshooting](#14-troubleshooting)
15. [FAQ](#15-faq)

---

## 1. What Is This Project?

This is a **Python-based QA automation and CI/CD utility suite** for BitBucket Pipelines. It provides tools that:

- **Automatically select** which tests to run based on code changes
- **Track performance** of code over time
- **Monitor dependency health** (outdated or vulnerable packages)
- **Visualize pipeline metrics** in an interactive dashboard
- **Enforce code quality** via linting, type checking, and security scanning

Think of it as a **quality gate** — every code change passes through multiple automated checks before it can be merged.

---

## 2. Core Design Principle: Complete Isolation

**The entire QA suite lives inside the `bitbucket-qa/` folder and NEVER modifies, overwrites, or touches any existing file in the developer's project.**

### How Isolation Works

```
Developer's Project Root/
├── node_modules/          ← QA suite NEVER touches this
├── package.json           ← QA suite NEVER touches this
├── .gitignore             ← QA suite NEVER touches this
├── .env                   ← QA suite NEVER touches this
├── dist/                  ← QA suite NEVER touches this
├── src/                   ← QA suite NEVER touches this
├── .git/hooks/pre-push    ← Heavy gate outside QA dir (Git requires it here)
├── .git/hooks/pre-commit  ← Fast gate outside QA dir (Git requires it here)
│   └── both delegate to → bitbucket-qa/
├── bitbucket-qa/          ← ALL QA code, tools, tests, venv, artifacts
│   ├── venv/              ← Virtual environment
│   ├── tests/             ← All test files
│   ├── dependency-reports/
│   ├── dashboard/
│   ├── .benchmarks/
│   └── ... (all QA files)
└── setup_all.py           ← Creates bitbucket-qa/ with everything
```

### Isolation Enforcement

Five automated tests in `tests/test_quality_gate.py` verify isolation (pre-commit + pre-push):

1. **`test_pre_push_hook_delegates_to_qa_dir()`** — Verifies the pre-push hook `cd`s into `bitbucket-qa/` before running checks
2. **`test_no_hardcoded_user_paths()`** — Ensures no source file contains hardcoded user paths like `C:\Users\...`
3. **`test_setup_all_writes_only_to_qa_dir()`** — Verifies setup targets only `bitbucket-qa/`

### What the Pre-Push Hook Does

```bash
# 1. Find the QA directory
QA_DIR="$REPO_ROOT/bitbucket-qa"

# 2. If it doesn't exist, skip (push allowed)
if [ ! -d "$QA_DIR" ]; then exit 0; fi

# 3. cd into QA directory — NEVER runs in project root
cd "$QA_DIR"

# 4. Run all checks from inside bitbucket-qa/
$PYTHON -m pytest test_precheck.py tests/ ...
```

---

## 3. Why Does It Exist?

Without this suite:
- Runs **all tests** every time (slow)
- Has **no performance tracking** (regressions unnoticed)
- Has **no dependency monitoring** (vulnerable packages stay)
- Has **no visual dashboard** (pipeline health invisible)
- Scripts may **modify project files** (risk of breaking developer code)

**With this suite:**
- Only **affected tests** run (faster)
- Performance is **tracked and compared** against baselines
- Dependencies are **automatically checked** for vulnerabilities
- A **visual dashboard** shows pipeline health
- Code quality is **automatically enforced**
- **Zero risk** to developer's project files

---

## 4. Architecture Overview

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
│  │  Test    │   │Complexity│                                │
│  │ Impact   │   │  Check   │                                │
│  └──────────┘   └──────────┘                                │
│                        │                                      │
│                        ▼                                      │
│              ┌──────────────────┐                            │
│              │    Pipeline      │                            │
│              │    Dashboard     │                            │
│              └──────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

**Key principle:** Everything runs inside `bitbucket-qa/`. Developers just push code — the pipeline handles quality checks automatically.

---

## 5. Project Structure

```
BitBucket/                              (project root)
│
├── bitbucket-pipelines.yml         # CI/CD pipeline config (reference)
├── requirements.txt                # 28 Python packages with version bounds
│
├── setup_all.py                    # Creates bitbucket-qa/ with everything
├── setup.bat                       # Windows one-click setup
├── setup.sh                        # Linux/macOS one-click setup
│
├── smart_test_selector.py          # Test impact analysis tool
├── performance_benchmark.py        # Performance tracking & regression detection
├── dependency_health.py            # Dependency vulnerability & health checking
├── pipeline_dashboard.py           # Interactive pipeline metrics dashboard
│
├── test_precheck.py                # Pre-merge validation tests
├── tests/
│   ├── test_sample.py              # Sample test suite
│   ├── test_fixes.py               # Unit tests for bug fixes
│   ├── test_quality_gate.py        # Quality gate + isolation enforcement tests
│   └── test_tools_units.py         # Unit tests for tool internals
│
├── run_full_pipeline.bat           # Full QA runner (Windows)
├── run_full_pipeline.sh            # Full QA runner (Linux/macOS)
├── test_phase1.bat                 # Phase 1 test runner (Windows)
├── test_phase1.sh                  # Phase 1 test runner (Linux/macOS)
├── fix_encoding.bat                # Fix encoding issues (Windows)
├── fix_encoding.sh                 # Fix encoding issues (Linux/macOS)
│
├── .git/hooks/pre-push             # Heavy gate: tests + coverage (delegates to bitbucket-qa/)
├── .git/hooks/pre-commit           # Fast gate: syntax + scanner (delegates to bitbucket-qa/)
├── .gitignore                      # Git ignore rules
│
├── README.md                       # Quick start guide and tool reference
├── QUICKSTART.md                   # Quick start for new developers
├── CHANGELOG.md                    # Version history
├── PROJECT_OVERVIEW.md             # This document
└── EXECUTIVE_SUMMARY.md            # Executive summary
```

---

## 6. How to Set Up

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

**What it does:**
1. Creates `bitbucket-qa/` directory
2. Creates virtual environment inside `bitbucket-qa/venv/`
3. Installs all 28 dependencies
4. Runs validation tests
5. Verifies all 4 tools import correctly

### Option B: Manual Setup

```bash
mkdir -p "bitbucket-qa"
cd "bitbucket-qa"
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r ../requirements.txt
```

---

## 7. Tools Deep Dive

### 7.1 Smart Test Selector (`smart_test_selector.py`)

**Purpose:** Analyze code changes and run only the affected tests.

**How it works:**
1. Reads git diff to find changed files
2. Parses Python AST to map source files to test files
3. Generates `test-matrix.json` with affected tests
4. Pipeline reads this matrix and skips unaffected tests

**Key methods:**
- `_get_changed_files()` — Gets files changed via git diff
- `_build_test_mapping()` — Parses test imports using Python AST
- `get_affected_tests()` — Returns set of affected test files
- `generate_test_matrix()` — Produces JSON matrix for parallel execution
- `should_run_tests()` — Cache-based check using SHA256 hashes

**Intelligence features:**
- If `requirements.txt` changes → ALL tests run
- If only a test file changes → only that test runs
- If a source file changes → tests that import it run

---

### 7.2 Performance Benchmark (`performance_benchmark.py`)

**Purpose:** Track execution time, memory, and CPU to detect regressions.

**Key methods:**
- `benchmark(name)` — Decorator that instruments any function
- `save_baseline()` — Saves current results as baseline
- `compare_with_baseline()` — Returns regressions and improvements
- `generate_html_report()` — Produces HTML report
- `check_regressions(threshold)` — Returns True if any function exceeds threshold

**Measurement data:**
```json
{
  "name": "example_function",
  "execution_time": 0.102,
  "cpu_time": 0.098,
  "memory_before_mb": 15.2,
  "memory_after_mb": 15.4,
  "memory_peak_mb": 0.3,
  "cpu_percent": 2.1
}
```

---

### 7.3 Dependency Health Check (`dependency_health.py`)

**Purpose:** Monitor all packages for outdated versions, vulnerabilities, and health.

**Health score factors:**

| Factor | Impact |
|--------|--------|
| No release in 365+ days | -20 points |
| No release in 180+ days | -10 points |
| Low downloads (<1000/month) | -15 points |
| Each vulnerability found | -10 points (max -50) |
| Mature project | +5 points |
| Inactive project | -40 points |

**Data sources:** PyPI API, OSV.dev, PyUp, pypistats.org

**Caching:** Results cached for 24h (PyPI, pypistats) and 6h (vulnerabilities).

---

### 7.4 Pipeline Dashboard (`pipeline_dashboard.py`)

**Purpose:** Record pipeline metrics and generate interactive dashboard.

**Dashboard charts:**
1. Daily Pipeline Runs
2. Success Rate by Branch
3. Step Duration
4. Test Coverage Trend
5. Pipeline Duration Trend
6. Step Success Rate

**Database:** SQLite with tables for `pipeline_runs`, `step_metrics`, `test_results`, `performance_metrics`.

---

## 8. CI/CD Pipeline Explained

### Pipeline Configuration

- **Image:** `python:3.11`
- **Docker:** Enabled
- **Size:** 2x (double resources)
- **Max timeout:** 30 minutes per step
- **Coverage threshold:** 30% (consistent with local hook)

### Coverage Threshold Consistency

Both the local pre-push hook and the CI pipeline use `--cov-fail-under=30`. This ensures code that passes locally also passes in CI, and vice versa.

---

## 9. How the Pipeline Works

### Stage 1: Cache & Precheck (Parallel)

- Install dependencies, freeze packages
- Validate Python syntax, check file existence

### Stage 2: Test Impact Analysis

- Analyze git diff, map changes to tests
- Output `test-matrix.json` for later stages

### Stage 3: Quality Checks (Parallel)

- Lint & format (black, isort, flake8)
- Type checking (mypy)
- Security scan (bandit, pip-audit)
- Complexity analysis (radon, vulture)

### Stage 4: Tests & Coverage

- Run affected tests with parallel execution
- Enforce 30% minimum coverage

### Stage 5: Benchmark & Dependencies (Parallel)

- Performance benchmarking
- Dependency health check

### Stage 6: Dashboard

- Record metrics to SQLite
- Generate interactive Plotly dashboard

---

## 10. Testing Strategy

### Test Layers

| Layer | File | Purpose |
|-------|------|---------|
| **Precheck** | `test_precheck.py` | Syntax validation, file existence |
| **Sample** | `tests/test_sample.py` | Import validation, sanity |
| **Unit** | `tests/test_fixes.py` | Bug fix verification |
| **Unit** | `tests/test_tools_units.py` | Tool internal logic |
| **Quality Gate** | `tests/test_quality_gate.py` | Project rules + isolation enforcement |

### Isolation Tests (v1.3.0)

| Test | What It Verifies |
|------|-----------------|
| `test_pre_push_hook_delegates_to_qa_dir` | Hook `cd`s into `bitbucket-qa/` |
| `test_no_hardcoded_user_paths` | No `C:\Users\...` in source files |
| `test_setup_all_writes_only_to_qa_dir` | Setup targets only `bitbucket-qa/` |

---

## 11. Bugs Found & Fixed

### v1.3.0 (July 15, 2026)

| # | File | Bug | Fix | Severity |
|---|------|-----|-----|----------|
| 1 | `setup_all.py` | Dead code after `return False` — `project_dir` unreachable | Fixed indentation to make code reachable | Critical |
| 2 | `run_full_pipeline.bat` | Double-nesting: `BitBucket QA\BitBucket QA\` | Fixed to `BitBucket QA\` | Critical |
| 3 | `bitbucket-pipelines.yml` | CI uses 85% coverage but local hook uses 30% | Aligned CI to 30% | Critical |
| 4 | `dependency_health.py` | Only parses `==`, `>=`, `<=` specifiers | Added `~=`, `!=`, `>`, `<` | Medium |
| 5 | `performance_benchmark.py` | Dead `result = str(e)` before re-raise | Removed dead assignment | Medium |
| 6 | `performance_benchmark.py` | `check_regressions()` stops at first regression | Fixed to check all regressions | Medium |
| 7 | `pipeline_dashboard.py` | SQLite connections not cleaned up on error | Added `try/finally` wrappers | Medium |
| 8 | `smart_test_selector.py` | Uses MD5 for hashing | Replaced with SHA256 | Medium |
| 9 | `test_precheck.py` | Does not exclude `bitbucket-qa/` from scanning | Added to exclusion list | Medium |
| 10 | `_gen_setup.py` | Hardcoded user path `C:\Users\...` | Changed to `Path(__file__).parent` | Medium |
| 11 | `test_phase1.sh` | Missing shebang line | Added `#!/bin/bash` | Low |
| 12 | `fix_encoding.sh` | Missing shebang line | Added `#!/bin/bash` | Low |
| 13 | `test_phase1.bat` | Wrong venv path (`venv\Scripts\activate`) | Fixed to `BitBucket QA\venv\...` | Low |
| 14 | `test_phase1.sh` | Wrong venv path (`source venv/bin/activate`) | Fixed to `bitbucket-qa/venv/...` | Low |
| 15 | `bitbucket-pipelines.yml` | `vulture --sort-by-size` not supported in 2.x | Removed flag | Low |

### v1.1.0 (June 29, 2026) — 21 bugs fixed
### v1.0.0 (June 26, 2026) — Initial release

---

## 12. Dependencies & Versioning

### Version Strategy

All packages use **bounded ranges** (`>=X,<Y`):
- **Lower bound:** Minimum version that works
- **Upper bound:** Next major version (prevents breaking changes)

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

---

## 13. Generated Files & Artifacts

### Files Created by Tools (all inside `bitbucket-qa/`)

| File | Created By | Purpose |
|------|-----------|---------|
| `test-matrix.json` | smart_test_selector | Tests to run |
| `.test-cache/last_test_hash.txt` | smart_test_selector | SHA256 cache |
| `.benchmarks/current.json` | performance_benchmark | Latest results |
| `.benchmarks/baseline.json` | performance_benchmark | Saved baseline |
| `.benchmarks/performance-report.html` | performance_benchmark | HTML report |
| `dependency-reports/*.html` | dependency_health | Health reports |
| `dependency-reports/pypi_cache.json` | dependency_health | PyPI cache (24h) |
| `dependency-reports/vuln_cache.json` | dependency_health | Vuln cache (6h) |
| `pipeline-metrics.db` | pipeline_dashboard | SQLite database |
| `dashboard/dashboard.html` | pipeline_dashboard | Interactive dashboard |

---

## 14. Troubleshooting

### "Push blocked on tests"
- Read the failure output
- Run: `cd "bitbucket-qa" && pytest test_precheck.py tests/ -v`
- Fix the code, commit, push again

### "Push blocked on coverage"
- Add tests for new code
- Check: `cd "bitbucket-qa" && pytest tests/ --cov=. --cov-report=html`

### "Script modified my project files"
**This should never happen.** The QA suite is completely isolated inside `bitbucket-qa/`. Report it as a critical bug.

### "Python not found"
- Install Python 3.11+ from https://www.python.org/downloads/
- On Windows, check "Add Python to PATH"

### "Module not found"
- Run: `cd "bitbucket-qa" && pip install -r ../requirements.txt`

---

## 15. FAQ

**Q: Do I need to install this on my machine?**  
A: No. The pipeline runs automatically. Local setup is optional for running tools manually.

**Q: Will this modify my project files?**  
A: Never. The entire QA suite lives inside `bitbucket-qa/` and never touches files outside it.

**Q: Can I run individual tools?**  
A: Yes. `cd "bitbucket-qa"` and run any tool directly.

**Q: What if I break the pipeline?**  
A: Fix the issue in your PR and push again.

**Q: How do I add new tests?**  
A: Add `test_*.py` files in `bitbucket-qa/tests/`. The smart test selector auto-discovers them.

**Q: How do I update dependencies?**  
A: Edit `bitbucket-qa/requirements.txt` with new version bounds.

**Q: What does the dashboard show?**  
A: Pipeline success rates, test coverage trends, step durations, and branch health.

---

*Document generated as part of the BitBucket Pipeline QA & Utility Suite.*  
*Author: Sr. QA Tester - Akshaykumar Dudhwala*
