"""
Pre-push validation tests.

Scans the ACTUAL PROJECT CODE for:
  - Syntax errors (Python + TypeScript)
  - Unused imports
  - Bare except clauses
  - Trailing whitespace
  - Long lines
  - Missing newlines
  - Empty files
  - Double semicolons

Output: file:line:severity:message for every issue found.
"""

import os
import subprocess
import sys

import pytest

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _find_repo_root(start: str) -> str:
    """Resolve git work-tree root robustly."""
    try:
        out = subprocess.check_output(
            ["git", "-C", start, "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).strip()
        if out and os.path.isdir(out):
            return os.path.abspath(out)
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        pass

    candidate = start
    while True:
        if os.path.isdir(os.path.join(candidate, ".git")):
            return candidate
        parent = os.path.dirname(candidate)
        if parent == candidate:
            break
        candidate = parent
    return start


def _find_suite_root(start: str) -> str:
    """Directory that holds the QA suite (code_scanner + requirements)."""
    markers = ("code_scanner.py", "requirements.txt")
    candidate = start
    while True:
        if all(os.path.isfile(os.path.join(candidate, m)) for m in markers):
            return candidate
        parent = os.path.dirname(candidate)
        if parent == candidate:
            break
        candidate = parent
    return start


REPO_ROOT = _find_repo_root(BASE_DIR)
SUITE_ROOT = _find_suite_root(BASE_DIR)

# When installed via setup_all into bitbucket-qa/, scan the parent project.
# When developing this repo itself, suite root == repo root.
if os.path.basename(SUITE_ROOT) == "bitbucket-qa":
    PROJECT_ROOT = os.path.dirname(SUITE_ROOT)
else:
    PROJECT_ROOT = REPO_ROOT


def get_project_files():
    """Get all scannable source files in the project."""
    files = []
    exclude_dirs = {
        "venv", ".venv", "__pycache__", "__pypackages__",
        ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache",
        "node_modules", "dist", "build", ".next", ".nuxt",
        "htmlcov", "coverage", "dashboard",
        "dependency-reports", "test-results",
        "bitbucket-qa",
    }

    for root, dirs, filenames in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for fn in filenames:
            if fn.endswith((".py", ".ts", ".js", ".tsx", ".jsx")):
                files.append(os.path.join(root, fn))
    return sorted(files)


def get_qa_files():
    """Get Python files inside the QA suite itself."""
    files = []
    exclude_dirs = {
        "venv", ".venv", "__pycache__", ".pytest_cache",
        ".git", "tests", "bitbucket-qa",
    }
    for root, dirs, filenames in os.walk(SUITE_ROOT):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for fn in filenames:
            if fn.endswith(".py") and fn not in ("test_precheck.py",):
                files.append(os.path.join(root, fn))
    return files


# ======================================================================
#  TEST 1: Run the actual code scanner on the project
# ======================================================================


def test_code_scanner_passes():
    """Run code_scanner.py on the project and verify zero errors."""
    scanner_path = os.path.join(SUITE_ROOT, "code_scanner.py")
    if not os.path.exists(scanner_path):
        pytest.skip("code_scanner.py not found")

    result = subprocess.run(
        [sys.executable, scanner_path, PROJECT_ROOT],
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    print("\n" + output)

    assert result.returncode == 0, (
        f"Code scanner found errors. Output:\n{output}"
    )


# ======================================================================
#  TEST 2: Python syntax check on every project .py file
# ======================================================================


@pytest.mark.parametrize("file_path", get_project_files())
def test_file_syntax(file_path):
    """Verify every source file has valid syntax."""
    import ast

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    # Python files: use ast.parse
    if file_path.endswith(".py"):
        try:
            ast.parse(source, filename=file_path)
        except SyntaxError as e:
            pytest.fail(
                f"SYNTAX ERROR in {file_path}:{e.lineno}: {e.msg}"
            )

    # Non-empty check
    assert source.strip(), f"File is empty: {file_path}"


# ======================================================================
#  TEST 3: QA suite structure checks
# ======================================================================


def test_no_empty_qa_python_files():
    """Ensure no empty Python files exist in QA suite."""
    for file_path in get_qa_files():
        assert os.path.getsize(file_path) > 0, f"Empty file: {file_path}"


def test_requirements_exists():
    """Ensure requirements.txt exists."""
    req_path = os.path.join(SUITE_ROOT, "requirements.txt")
    assert os.path.exists(req_path), "requirements.txt not found in QA directory"


def test_bitbucket_pipelines_exists():
    """Ensure bitbucket-pipelines.yml exists."""
    yml_path = os.path.join(SUITE_ROOT, "bitbucket-pipelines.yml")
    assert os.path.exists(yml_path), "bitbucket-pipelines.yml not found"


def test_code_scanner_exists():
    """Ensure code_scanner.py exists."""
    assert os.path.exists(os.path.join(SUITE_ROOT, "code_scanner.py")), (
        "code_scanner.py not found - required for project code scanning"
    )


# ======================================================================
#  TEST 4: No hardcoded user paths
# ======================================================================


@pytest.mark.parametrize("file_path", get_qa_files())
def test_no_hardcoded_user_paths(file_path):
    """No source file should contain hardcoded user-specific paths."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    assert "C:\\Users\\" not in src and "C:/Users/" not in src, (
        f"Hardcoded user path found in {file_path}"
    )
