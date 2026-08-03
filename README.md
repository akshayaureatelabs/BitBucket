# BitBucket Pipeline QA & Utility Suite

A collection of Python-based tools and configurations that validate every code change **locally** before it is pushed. The project acts as a **quality gate** — nothing is pushed unless the local checks pass. (BitBucket Pipelines CI is supported but **not required**; the local pre-push hook is the primary gate.)

---

## Core Design Principle: Complete Isolation

**Two layers — keep them straight:**

| Layer | Location | Role |
|-------|----------|------|
| **Source of truth** | **This GitHub repo root** | Develop and version the QA suite here (`code_scanner.py`, hooks, tests, tools). |
| **Deploy / isolation** | **`bitbucket-qa/` inside a consumer project** | Created by `setup_all.py`. All runtime tools, venv, and artifacts live here so the consumer's app files are never touched. |

- Hooks install under `.git/hooks/` (Git requires that) and only `cd` into `bitbucket-qa/`.
- Consumer files (`node_modules`, `.env`, app source, etc.) are never modified by the suite.
- After pulling updates to this repo, refresh embeds then redeploy:

```bash
python _gen_setup.py    # refresh EMBEDDED_FILES from live sources
python setup_all.py     # write bitbucket-qa/ + install + validate
```

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
git commit -m "your message"   # pre-commit: staged .py syntax only
git push                        # pre-push: full scanner + tests + coverage >= 30%
```
**Two-layer quality gate:**
- **On commit** (`pre-commit`): Fast check — syntax validation on **staged** Python files only (Unix + Windows).
- **On push** (`pre-push`): Full code scanner + QA tests + coverage >= 30%.
- *If **checks pass** → commit/push proceeds.*
- *If **any check fails** → commit/push is **blocked** and you must fix it first.*

### If Commit Is Blocked (pre-commit)
```bash
# Fix the syntax errors, then re-add and commit
git add -A
git commit -m "your message"
```

### If Push Is Blocked (pre-push)
```bash
cd "bitbucket-qa"
python -m pytest test_precheck.py -v
python -m pytest tests/ -v
python -m pytest tests/ --cov=. --cov-report=html
git push
```

### Extra Commands
```bash
cd "bitbucket-qa"
python dependency_health.py --check-all --generate-report
python pipeline_dashboard.py --simulate-data
python performance_benchmark.py --run-benchmarks
python smart_test_selector.py --summary --generate-matrix
```

---

## Overview

- **Smart Test Selection** — Analyze code changes to run only relevant tests
- **Performance Benchmarking** — Track and compare execution metrics over time
- **Dependency Health** — Monitor package health and vulnerabilities
- **Pipeline Dashboard** — Interactive Plotly reports (SQLite + foreign keys)
- **Security & Quality** — Linting, type checking, and security scanning

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- `pip`
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

### Manual Setup

```bash
mkdir -p "bitbucket-qa"
cd "bitbucket-qa"
python -m venv venv
# Windows: venv\Scripts\activate
# Linux / macOS: source venv/bin/activate
pip install -r ../requirements.lock   # reproducible
# or: pip install -r ../requirements.txt
```

---

## Local Quality Gate

| Hook | What runs | Blocks on |
|------|-----------|-----------|
| **pre-commit** | Staged `.py` syntax only | Syntax errors |
| **pre-push** | Full `code_scanner` + tests + coverage ≥ 30% | Any failure |

Coverage threshold is **30%** locally and in CI.

---

## Tools

Run from inside `bitbucket-qa/` using the venv Python. See prior sections for flags (`smart_test_selector`, `performance_benchmark`, `dependency_health`, `pipeline_dashboard`).

---

## Testing

```bash
cd "bitbucket-qa"
pytest test_precheck.py tests/ -v
pytest tests/ --cov=. --cov-report=html
```

Includes `tests/test_scanner_exit.py` to ensure ERROR findings yield a non-zero process exit (quality-gate regression guard).

---

## Optional: BitBucket Pipelines CI

`bitbucket-pipelines.yml` is a reference CI config. Complexity (radon/vulture) steps are hard gates (no `|| true`). Coverage fail-under is 30%.

---

## Project Structure

```
BitBucket/                      # SOURCE OF TRUTH for the QA suite
├── setup_all.py                # Creates bitbucket-qa/ in a consumer project
├── _gen_setup.py               # Regenerates setup_all EMBEDDED_FILES
├── code_scanner.py             # Real issue scanner (exit 1 on ERROR)
├── hooks/pre-commit[.bat]      # Staged syntax only
├── hooks/pre-push[.bat]        # Full gate
├── requirements.txt / .lock
├── tests/
└── ...
```

Deployed consumer layout:

```
my-app/
├── bitbucket-qa/               # ISOLATED suite (venv + tools + artifacts)
├── .git/hooks/pre-commit       # delegates into bitbucket-qa/
├── .git/hooks/pre-push
└── (your application files untouched)
```

---

## Troubleshooting

### Stale tools after pull
```bash
python _gen_setup.py
python setup_all.py
```

### Push blocked
Fix failures shown by the hook; re-run tests under `bitbucket-qa/`.

### Wrong Python in hooks
Re-run `python setup_all.py` so hooks use `bitbucket-qa/venv`.

---

## Contributing

**Author:** Sr. QA Tester - Akshaykumar Dudhwala

1. Branch from `main`
2. Change suite sources at **repo root**
3. Run `python _gen_setup.py` if embeds must change
4. `pytest test_precheck.py tests/ -v`
5. Push (pre-push gate validates)
