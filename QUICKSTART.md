# Quick Start Guide

> This guide is for new developers setting up the project for the first time.

---

## Core Principle

**Everything stays inside `bitbucket-qa/`** — the QA suite NEVER modifies your project files. If you have `node_modules`, `package.json`, `.env`, `dist/`, or any other files, they remain untouched.

---

## First Time Setup

```bash
git clone <repo-url>
cd <repo-folder>
python setup_all.py
```

This creates the `bitbucket-qa/` directory with:
- A virtual environment (`bitbucket-qa/venv/`)
- All dependencies installed
- All QA tools and tests ready

---

## Daily Workflow

```bash
git add -A
git commit -m "your message"
git push
```

When you `git push`, the pre-push hook runs automatically from inside `bitbucket-qa/`:
- If all tests pass and coverage >= 30% → push proceeds
- If anything fails → push is blocked, you must fix it first

---

## If Push Is Blocked

```bash
cd "bitbucket-qa"

# Check what failed
python -m pytest test_precheck.py -v   # syntax check
python -m pytest tests/ -v             # full test suite

# Fix the code, commit, then push again
git push
```

---

## Extra Commands

```bash
cd "bitbucket-qa"
python dependency_health.py --check-all --generate-report    # Dependency health check
python pipeline_dashboard.py --simulate-data                # Dashboard generate
python performance_benchmark.py --run-benchmarks            # Performance benchmark
python smart_test_selector.py --summary --generate-matrix   # Test impact analysis
```

---

## Project Structure

```
BitBucket/
├── bitbucket-pipelines.yml    # CI/CD pipeline (optional)
├── requirements.txt           # Python dependencies
├── setup_all.py               # Creates bitbucket-qa/
├── smart_test_selector.py     # Test impact analysis
├── performance_benchmark.py   # Performance tracking
├── dependency_health.py       # Dependency health check
├── pipeline_dashboard.py      # Pipeline dashboard
├── test_precheck.py           # Pre-merge validation
├── tests/
│   ├── test_sample.py         # Sample tests
│   ├── test_fixes.py          # Unit tests for fixes
│   ├── test_quality_gate.py   # Quality gate tests
│   └── test_tools_units.py    # Tool unit tests
├── .git/hooks/pre-push        # Quality gate (delegates to bitbucket-qa/)
├── CHANGELOG.md               # Version history
├── PROJECT_OVERVIEW.md        # Complete documentation
├── README.md                  # Detailed guide
└── QUICKSTART.md              # This file
```

---

## Pipeline Stages (What Runs on BitBucket)

```
Stage 1: Cache & Precheck     → Syntax check + file validation
Stage 2: Test Impact Analysis → Determines which tests to run
Stage 3: Quality Checks       → Lint, Type, Security, Complexity
Stage 4: Tests & Coverage     → 30% minimum coverage required
Stage 5: Benchmark & Deps     → Performance + dependency check
Stage 6: Dashboard            → Metrics are generated
```

---

## Common Issues

### "Python not found"
```bash
python --version   # Windows
python3 --version  # Linux/Mac
```
Install Python 3.11 or higher.

### "Module not found"
```bash
cd "bitbucket-qa"
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac
pip install -r ../requirements.txt
```

### "Tests failing"
```bash
cd "bitbucket-qa"
python -m pytest test_precheck.py -v
python -m pytest tests/ -v
```

### "Script modified my files"
**This should never happen.** The QA suite is completely isolated inside `bitbucket-qa/`. Report it as a bug.

---

## Help
- **README.md** — Detailed documentation
- **PROJECT_OVERVIEW.md** — Complete technical overview
- **CHANGELOG.md** — Version history and bug fixes

---

*Created by: Sr. QA Tester - Akshaykumar Dudhwala*
