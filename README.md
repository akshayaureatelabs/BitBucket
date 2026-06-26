# BitBucket Pipeline QA & Utility Suite

A comprehensive collection of Python-based tools and CI/CD configurations designed to optimize, monitor, and validate BitBucket Pipelines.

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

- **Python 3.11+** (3.11 recommended for BitBucket Pipelines compatibility)
- `pip` (comes with Python)

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

The setup script will:
1. Create a virtual environment (`venv/`)
2. Install all dependencies from `requirements.txt`
3. Run validation tests (7 tests)
4. Verify all 4 tools import correctly

### Manual Setup

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

## Tools

All tools can be run from the project root after activating the virtual environment.

### 1. Smart Test Selector (`smart_test_selector.py`)

Analyzes code changes (via git diff) to determine which tests are affected, then generates a test matrix for targeted CI runs.

```bash
# Generate test matrix and print summary
python smart_test_selector.py --summary --generate-matrix

# Custom output file
python smart_test_selector.py --generate-matrix --output my-matrix.json
```

| Flag | Description |
|------|-------------|
| `--generate-matrix` | Generate `test-matrix.json` with affected test files |
| `--summary` | Print analysis summary to console |
| `-o, --output` | Output file path (default: `test-matrix.json`) |

**Output:** `test-matrix.json` — Used by the pipeline to skip unaffected tests.

---

### 2. Performance Benchmark (`performance_benchmark.py`)

Tracks execution time, memory usage, and CPU consumption. Compares against a saved baseline to detect regressions.

```bash
# Run benchmarks and generate HTML report
python performance_benchmark.py --run-benchmarks --generate-report

# Save current results as new baseline
python performance_benchmark.py --run-benchmarks --save-baseline

# Compare current results against saved baseline
python performance_benchmark.py --compare-baseline

# Check for regressions (default threshold: 10%)
python performance_benchmark.py --check-regressions 15.0
```

| Flag | Description |
|------|-------------|
| `--run-benchmarks` | Execute benchmark suite (5 iterations of example function) |
| `--compare-baseline` | Compare current results with saved baseline |
| `--save-baseline` | Save current results as the new baseline |
| `--generate-report` | Generate HTML report at `.benchmarks/performance-report.html` |
| `--check-regressions` | Check if any function regressed beyond threshold (%) |

**Output:** `.benchmarks/current.json`, `.benchmarks/performance-report.html`, `.benchmarks/baseline.json`

---

### 3. Dependency Health Check (`dependency_health.py`)

Checks for outdated packages, known vulnerabilities (via pip-audit), and overall dependency health.

```bash
# Full check with HTML report
python dependency_health.py --check-all --generate-report

# Fail if any issues found (useful in CI)
python dependency_health.py --check-all --fail-on-issues

# Export results to JSON
python dependency_health.py --check-all --output-json report.json
```

| Flag | Description |
|------|-------------|
| `--check-all` | Run all dependency checks |
| `--generate-report` | Generate HTML report |
| `--fail-on-issues` | Exit with non-zero code if issues found |
| `--output-json` | Export results to a JSON file |

**Output:** `dependency-reports/` directory with HTML/JSON reports.

---

### 4. Pipeline Dashboard (`pipeline_dashboard.py`)

Records pipeline run metrics to a SQLite database and generates an interactive Plotly-based HTML dashboard.

```bash
# Record current pipeline run metrics (uses BitBucket env vars)
python pipeline_dashboard.py --record-metrics

# Generate dashboard for last 30 days
python pipeline_dashboard.py --generate-dashboard --days 30

# Generate sample data for testing/preview
python pipeline_dashboard.py --simulate-data
python pipeline_dashboard.py --generate-dashboard --days 30
```

| Flag | Description |
|------|-------------|
| `--record-metrics` | Record current pipeline run to database |
| `--generate-dashboard` | Generate interactive HTML dashboard |
| `--simulate-data` | Insert 100 sample pipeline runs for testing |
| `--days` | Number of days to include (default: 30) |

**Output:** `dashboard/dashboard.html` (interactive charts), `pipeline-metrics.db` (SQLite database)

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run precheck validation (syntax, structure)
pytest test_precheck.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run tests in parallel
pytest tests/ -n auto
```

### Test Coverage

| Test | Description |
|------|-------------|
| `test_python_syntax` | Validates Python syntax of all `.py` files |
| `test_no_empty_python_files` | Ensures no empty Python files exist |
| `test_requirements_exists` | Checks `requirements.txt` exists |
| `test_pipeline_yml_exists` | Checks `bitbucket-pipelines.yml` exists |
| `test_sample` | Sample test placeholder |
| `test_imports` | Validates key imports work |

---

## Pipeline Configuration

The `bitbucket-pipelines.yml` defines the CI/CD pipeline with the following stages:

### Pipeline Stages

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

### Stage Details

| Stage | Tools Used | Purpose |
|-------|-----------|---------|
| **Smart Cache Setup** | pip | Install deps, freeze installed packages |
| **Pre-merge Validation** | pytest | Run syntax and structure checks |
| **Test Impact Analysis** | smart_test_selector.py | Determine which tests to run |
| **Lint & Format** | black, isort, flake8, pylint | Code quality checks |
| **Type Checking** | mypy | Static type analysis |
| **Security Scan** | bandit, pip-audit | Vulnerability and security checks |
| **Complexity & Dead Code** | radon, vulture | Code complexity and unused code detection |
| **Tests & Coverage** | pytest, pytest-cov | Run tests with 85% minimum coverage |
| **Performance Benchmark** | performance_benchmark.py | Track and compare performance |
| **Dependency Health** | dependency_health.py | Check dependency status |
| **Pipeline Dashboard** | pipeline_dashboard.py | Record metrics and generate dashboard |

### Triggers

| Trigger | Stages Executed |
|---------|----------------|
| **Pull Request** (any branch) | All 6 stages (full pipeline) |
| **Push to `main`** | All 6 stages (full pipeline) |
| **Push to other branches** | Stages 1, 3, 4 only (quick validation) |

### Pipeline Options

- **Docker:** Enabled
- **Max timeout:** 30 minutes per step
- **Resource size:** 2x (double CPU/memory)
- **Python image:** `python:3.11`
- **Caching:** pip packages + pytest cache

### Artifacts Generated

| Artifact | Generated By |
|----------|-------------|
| `installed-packages.txt` | Smart Cache Setup |
| `test-results/precheck.xml` | Pre-merge Validation |
| `test-matrix.json` | Test Impact Analysis |
| `lint-report.txt` | Lint & Format |
| `mypy-report.txt` | Type Checking |
| `bandit-report.json` | Security Scan |
| `pip-audit.json` | Security Scan |
| `radon-report.json` | Complexity Check |
| `vulture-report.txt` | Complexity Check |
| `.benchmarks/**` | Performance Benchmark |
| `dependency-reports/**` | Dependency Health |
| `pipeline-metrics.db` | Pipeline Dashboard |
| `dashboard/**` | Pipeline Dashboard |
| `coverage.xml`, `htmlcov/**` | Tests & Coverage |

---

## Project Structure

```
BitBucket/
├── bitbucket-pipelines.yml    # CI/CD pipeline configuration
├── requirements.txt           # Python dependencies (with version bounds)
├── setup.bat                  # One-click setup (Windows)
├── setup.sh                   # One-click setup (Linux/macOS)
├── test_precheck.py           # Pre-merge validation tests
├── tests/
│   └── test_sample.py         # Sample test suite
├── smart_test_selector.py     # Test impact analysis tool
├── performance_benchmark.py   # Performance tracking utility
├── dependency_health.py       # Dependency health checker
├── pipeline_dashboard.py      # Pipeline metrics & dashboard
├── fix_encoding.bat           # Fix encoding issues (Windows)
├── fix_encoding.sh            # Fix encoding issues (Linux)
├── test_phase1.bat            # Phase 1 test runner (Windows)
├── test_phase1.sh             # Phase 1 test runner (Linux)
├── test-matrix.json           # Generated test matrix
├── README.md                  # This file
├── .gitignore                 # Git ignore rules
└── venv/                      # Virtual environment (not in git)
```

---

## Troubleshooting

### Python Version Errors
If you see errors about `pkg_resources` or incompatible packages:
- Ensure you're using **Python 3.11+**
- Recreate the venv: delete `venv/` and run `setup.bat` or `setup.sh` again

### Encoding Issues
If files show garbled characters between Windows and Linux:
```bash
# Windows
fix_encoding.bat

# Linux
fix_encoding.sh
```

### SQLite "ambiguous column" Error
If you see `sqlite3.OperationalError: ambiguous column: date`:
- This was fixed in the current version
- Ensure you're using the latest code from `main`

### Pipeline Failing on Coverage
The pipeline requires **85% minimum test coverage**. If your changes reduce coverage:
- Add tests for new code
- Check coverage locally: `pytest tests/ --cov=. --cov-report=html`

---

## Dependencies

All dependencies use bounded version ranges (`>=X,<Y`) for:
- **Compatibility** — Works across Python 3.11 to 3.14
- **Stability** — Prevents unexpected breaking changes from major version bumps
- **Security** — Allows patch-level updates for vulnerability fixes

Key dependencies: pytest, black, flake8, mypy, bandit, pip-audit, pandas, plotly, GitPython, psutil.

---

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run locally: `pytest test_precheck.py tests/ -v`
4. Push — the pipeline will automatically validate your changes
5. Create a pull request

The pipeline will run the full validation suite on your PR automatically.
