# Developer Guide — BitBucket QA Suite

> **Author:** Sr. QA Tester — Akshaykumar Dudhwala
> **Version:** v1.5.3
> **Last Updated:** 2026-07-21

---

## Table of Contents

1. [What is this?](#1-what-is-this)
2. [First Time Setup](#2-first-time-setup)
3. [Daily Workflow](#3-daily-workflow)
4. [If Push is Blocked](#4-if-push-is-blocked)
5. [All Commands](#5-all-commands)
6. [How It Works (Under the Hood)](#6-how-it-works-under-the-hood)
7. [Troubleshooting](#7-troubleshooting)
8. [FAQ](#8-faq)

---

## 1. What is this?

This is a **local quality gate** that runs automatically when you `git push`. It catches code issues **before** they reach the remote repository.

**What it checks:**

| Check | When it runs | Blocks push? |
|-------|-------------|--------------|
| Syntax errors (`ast.parse`) | Every commit | YES |
| Unused imports | Every push | YES |
| Bare except clauses | Every push | YES |
| Code scanner (full repo) | Every push | YES |
| Unit tests | Every push | YES |
| Coverage >= 30% | Every push | YES |

**What it does NOT do:**

- Does NOT modify your project files
- Does NOT send code to any cloud (everything is local)
- Does NOT slow down your commit (pre-commit is < 5 seconds)

---

## 2. First Time Setup

### Step 1: Clone the repo

```bash
git clone <repo-url>
cd <repo-folder>
```

### Step 2: Run setup

```bash
python setup_all.py
```

This single command will:

1. Create `bitbucket-qa/` folder with all QA tools
2. Create a virtual environment (`bitbucket-qa/venv/`)
3. Install all dependencies from `requirements.txt`
4. Run validation tests to make sure everything works
5. Install git hooks (pre-commit + pre-push)

**Output you should see:**

```
==================================================
  bitbucket-qa Suite - One-Click Setup
==================================================

[1/6] Writing QA files...
  OK Written 20 QA files to 'bitbucket-qa/'

[2/6] Checking Python...
  OK Found python

[3/6] Setting up virtual environment...
  OK Virtual environment ready

[4/6] Installing dependencies...
  OK All dependencies installed

[5/6] Running validation tests...
  OK 56 passed, 5 skipped

[6/6] Installing git hooks...
  OK Pre-push hook installed to .git/hooks/pre-push
  OK Pre-commit hook installed to .git/hooks/pre-commit

==================================================
  Setup Complete!
==================================================
```

### Step 3: Verify installation

```bash
# Check hooks are installed
ls .git/hooks/pre-push
ls .git/hooks/pre-commit

# Check code scanner works
python code_scanner.py .

# Check tests pass
python -m pytest tests/ -v
```

---

## 3. Daily Workflow

### Normal development (99% of the time)

Just code and push normally. The hooks run automatically:

```bash
# Write your code
vim my_module.py

# Stage changes
git add my_module.py

# Commit (pre-commit hook runs automatically)
git commit -m "feat: add new feature"

# Push (pre-push hook runs automatically)
git push
```

**What happens during commit:**

```
git commit
    │
    ▼
pre-commit hook runs (< 5 seconds)
    ├─ Syntax check on staged .py files
    └─ Code scanner on staged files
        └─ If error → COMMIT BLOCKED
```

**What happens during push:**

```
git push
    │
    ▼
pre-push hook runs (30-60 seconds)
    ├─ Step 1/4: Code scanner (full repo)
    ├─ Step 2/4: QA unit tests
    ├─ Step 3/4: Coverage >= 30%
    └─ Step 4/4: Summary
        └─ If any step fails → PUSH BLOCKED
```

### Running tests manually

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_fixes.py -v

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=html

# Open coverage report in browser
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
```

### Running the full pipeline manually

```bash
# Windows
run_full_pipeline.bat

# Linux/Mac
./run_full_pipeline.sh

# Quick test runner
run.bat
```

---

## 4. If Push is Blocked

### Step 1: Read the error message

The hook will print exactly what failed:

```
>>> 1/4 Code Scanner (blocking)...

======================================================================
  PROJECT CODE SCAN
======================================================================

  [FAIL] my_module.py
    ! L15: Syntax error: invalid syntax
    ~ L22: Unused import 'os'

----------------------------------------------------------------------
  RESULT: BLOCKED — 1 error(s) must be fixed
----------------------------------------------------------------------

PUSH BLOCKED - Fix the errors above before pushing.
```

### Step 2: Fix the issues

```bash
# Fix syntax error at line 15
vim my_module.py  # Go to line 15, fix the syntax

# Remove unused import at line 22
# Delete the line: import os
```

### Step 3: Try push again

```bash
git add my_module.py
git commit -m "fix: syntax error"
git push
```

### Common blocking issues

| Issue | How to fix |
|-------|-----------|
| `Syntax error: invalid syntax` | Fix the Python syntax (missing colon, bracket, etc.) |
| `Unused import: 'X'` | Remove the unused import line |
| `Bare except clause` | Change `except:` to `except Exception:` |
| `No newline at end of file` | Add a blank line at the end of the file |
| `Tests failed` | Run `python -m pytest tests/ -v` to see which test failed |
| `Coverage below 30%` | Add more tests or remove untested code |

---

## 5. All Commands

### Setup Commands

```bash
python setup_all.py                    # Full setup (creates everything)
python setup_all.py --force            # Overwrite existing files
python setup_all.py --skip-tests       # Skip validation tests
```

### Testing Commands

```bash
python -m pytest tests/ -v             # Run all tests
python -m pytest tests/ -v --tb=short  # Run tests with short traceback
python -m pytest tests/ --cov=.        # Run with coverage
python -m pytest tests/ --cov=. --cov-fail-under=30  # Enforce 30% minimum
python -m pytest test_precheck.py -v   # Run precheck tests only
```

### Code Quality Commands

```bash
python code_scanner.py .               # Scan entire project
python code_scanner.py src/            # Scan specific directory
```

### Tool Commands

```bash
# Dependency health check
python dependency_health.py --check-all
python dependency_health.py --check-all --generate-report

# Performance benchmark
python performance_benchmark.py --run-benchmarks
python performance_benchmark.py --run-benchmarks --generate-report
python performance_benchmark.py --compare-baseline

# Pipeline dashboard
python pipeline_dashboard.py --record-metrics
python pipeline_dashboard.py --generate-dashboard --days 30

# Smart test selector
python smart_test_selector.py --generate-matrix --summary
```

### Full Pipeline Commands

```bash
./run_full_pipeline.sh                 # Linux/Mac (runs all 9 checks)
run_full_pipeline.bat                  # Windows (runs all 9 checks)
run.bat                                # Quick test runner
```

---

## 6. How It Works (Under the Hood)

### Git Hooks

Git hooks are scripts in `.git/hooks/` that run automatically:

```
.git/hooks/
├── pre-commit    ← Runs before every commit
└── pre-push      ← Runs before every push
```

**Exit code concept:**

```bash
# In the hook script:
if [ error_occurred ]; then
    exit 1   # Git sees this → BLOCKS the action
fi
exit 0        # Git sees this → ALLOWS the action
```

### Code Scanner (AST Parsing)

The code scanner uses Python's `ast` module to parse code without running it:

```python
import ast

# This converts code into a tree structure
tree = ast.parse("""
def foo():
    import os  # This import is unused
    return 1
""")

# The scanner walks the tree to find issues
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        # Found an import statement
        # Check if it's used anywhere
```

**Why AST?**

- Catches syntax errors without running the code
- Can detect unused imports by comparing imported vs used names
- Works on the entire file at once (fast)

### Coverage Measurement

```bash
pytest tests/ --cov=. --cov-fail-under=30
```

**How it works:**

1. `pytest-cov` attaches a "counter" to every line in your `.py` files
2. When tests run, each executed line gets marked as "covered"
3. Coverage = (covered lines / total lines) × 100
4. If coverage < 30%, pytest returns exit code 1
5. The pre-push hook detects this and blocks the push

### Virtual Environment

```
bitbucket-qa/venv/
├── Scripts/
│   └── python.exe    ← Windows
└── bin/
    └── python        ← Linux/Mac
```

**Why venv?**

- Isolates QA dependencies from your project
- Ensures consistent Python version
- Prevents dependency conflicts

---

## 7. Troubleshooting

### "Python not found"

```bash
# Check Python version
python --version    # Windows
python3 --version   # Linux/Mac

# Install Python 3.11+ if needed
# https://www.python.org/downloads/
```

### "Module not found"

```bash
# Go to QA directory
cd bitbucket-qa

# Activate venv
venv\Scripts\activate    # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### "Tests failing"

```bash
# See which tests fail
python -m pytest tests/ -v

# Run specific failing test
python -m pytest tests/test_fixes.py::TestStripExtras -v

# Check test output
python -m pytest tests/ -v --tb=long
```

### "Pre-commit hook not running"

```bash
# Check if hook exists
ls .git/hooks/pre-commit

# If missing, reinstall
python setup_all.py

# Or manually copy
cp hooks/pre-commit .git/hooks/pre-commit
```

### "Pre-push hook not running"

```bash
# Check if hook exists
ls .git/hooks/pre-push

# If missing, reinstall
python setup_all.py

# Or manually copy
cp hooks/pre-push .git/hooks/pre-push
```

### "Coverage below 30%"

```bash
# See current coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Add tests for uncovered files
# Then re-run
python -m pytest tests/ --cov=. --cov-fail-under=30
```

### "Code scanner finding issues"

```bash
# Run scanner to see all issues
python code_scanner.py .

# Fix each issue:
# - Unused import → Remove the import line
# - Bare except → Change to except Exception:
# - Syntax error → Fix the Python syntax
```

---

## 8. FAQ

### Q: Does this slow down my workflow?

**A:** Pre-commit is < 5 seconds (only checks staged files). Pre-push is 30-60 seconds (full repo scan). Both run automatically — no extra commands needed.

### Q: Can I skip the hooks?

**A:** Yes, but not recommended:

```bash
# Skip pre-commit (not recommended)
git commit --no-verify -m "message"

# Skip pre-push (not recommended)
git push --no-verify
```

### Q: What if I need to commit broken code?

**A:** Use `--no-verify` temporarily, but fix it before pushing:

```bash
git commit --no-verify -m "WIP: work in progress"
# ... fix the code later ...
git add .
git commit -m "fix: completed feature"
git push  # Hook runs here
```

### Q: Can I add my own checks?

**A:** Yes! Edit the hook files:

```bash
# Add custom check to pre-push
vim .git/hooks/pre-push

# Add after line 48:
echo ">>> Custom check..."
$PYTHON my_custom_check.py
if [ $? -ne 0 ]; then
    echo "PUSH BLOCKED - Custom check failed."
    exit 1
fi
```

### Q: How do I update the QA suite?

```bash
# Re-run setup (won't overwrite existing files)
python setup_all.py

# Force overwrite all files
python setup_all.py --force
```

### Q: Can I use this in CI/CD?

**A:** Yes! The `bitbucket-pipelines.yml` file configures Bitbucket Pipelines to run the same checks in the cloud.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│                    DAILY WORKFLOW                        │
├─────────────────────────────────────────────────────────┤
│  1. Code your changes                                   │
│  2. git add .                                           │
│  3. git commit -m "message"    ← pre-commit runs        │
│  4. git push                  ← pre-push runs           │
│                                                         │
│  If commit blocked → Fix syntax, try again               │
│  If push blocked   → Fix errors, try again              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    USEFUL COMMANDS                       │
├─────────────────────────────────────────────────────────┤
│  python setup_all.py              # Setup                │
│  python code_scanner.py .         # Scan code            │
│  python -m pytest tests/ -v       # Run tests            │
│  run.bat                          # Quick test           │
│  run_full_pipeline.bat            # Full pipeline        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    IF SOMETHING BREAKS                   │
├─────────────────────────────────────────────────────────┤
│  1. Read the error message (it tells you what to fix)   │
│  2. Fix the issue                                       │
│  3. Try again                                           │
│  4. If stuck: python -m pytest tests/ -v (see details)  │
└─────────────────────────────────────────────────────────┘
```

---

*Created by: Sr. QA Tester — Akshaykumar Dudhwala*
*Version: 1.5.3*
