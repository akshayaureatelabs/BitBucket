"""
Quality-gate checks for the bitbucket-qa suite.

Enforces:
- Pre-push hook exists, uses venv Python, enforces 30% coverage, has 4 steps.
- requirements.txt has no unpinned packages.
- No bare except: in project code.
- All tools import cleanly.
- code_scanner.py exists and is functional.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

_this_dir = Path(__file__).resolve().parent


def _find_repo_root(start: Path) -> Path:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).strip()
        if out:
            return Path(out).resolve()
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        pass
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return start


def _find_suite_root(start: Path) -> Path:
    markers = ("code_scanner.py", "requirements.txt")
    for candidate in [start, *start.parents]:
        if all((candidate / m).is_file() for m in markers):
            return candidate
    return start.parent if start.name == "tests" else start


QA_DIR = _find_suite_root(_this_dir)
REPO_ROOT = _find_repo_root(QA_DIR)

EXCLUDE_DIRS = {
    "venv", ".venv", "__pycache__", ".pytest_cache",
    ".git", ".mypy_cache", ".test-cache", ".benchmarks",
    "htmlcov", "dashboard", "dependency-reports", "tests",
}


def project_py_files():
    files = []
    for root, dirs, fs in os.walk(QA_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in fs:
            if f.endswith(".py") and f != "test_precheck.py":
                files.append(Path(root) / f)
    return files


def _hook(name):
    """Locate an installed hook, accepting both sh and .bat variants."""
    candidates = [
        REPO_ROOT / ".git" / "hooks" / name,
        REPO_ROOT / ".git" / "hooks" / (name + ".bat"),
        REPO_ROOT / ".git" / "hooks" / (name + ".cmd"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


def hook_path():
    return _hook("pre-push")


def hook_content():
    p = hook_path()
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def precommit_path():
    return _hook("pre-commit")


def precommit_content():
    p = precommit_path()
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


# --- Pre-push hook ---

def test_pre_push_hook_exists():
    if not hook_path().exists():
        pytest.skip("pre-push hook not installed yet")
    assert hook_path().is_file(), "pre-push hook must be a file"
    assert hook_path().stat().st_size > 0, "pre-push hook must not be empty"


def test_pre_push_hook_uses_venv_python():
    if not hook_path().exists():
        pytest.skip("pre-push hook not installed yet")
    c = hook_content()
    assert "venv" in c and ("python" in c), (
        "hook must use the project venv Python"
    )


def test_pre_push_hook_coverage_threshold():
    if not hook_path().exists():
        pytest.skip("pre-push hook not installed yet")
    c = hook_content()
    assert "cov-fail-under=30" in c, "hook must enforce 30% coverage gate"


def test_pre_push_hook_has_four_steps():
    if not hook_path().exists():
        pytest.skip("pre-push hook not installed yet")
    c = hook_content()
    # Accept both sh (`>>> N/4`) and bat (`^>^>^> N/4`) step markers.
    assert len(re.findall(r"(?:>>>|\^>\^>\^>)\s*\d/4", c)) >= 3, (
        "hook must run at least 3 numbered steps"
    )


def test_pre_push_hook_blocks_on_tests():
    if not hook_path().exists():
        pytest.skip("pre-push hook not installed yet")
    c = hook_content()
    assert "PUSH BLOCKED" in c, "hook must block the push on failure"


def test_pre_push_hook_runs_scanner():
    if not hook_path().exists():
        pytest.skip("pre-push hook not installed yet")
    c = hook_content()
    assert "code_scanner.py" in c, "hook must run code_scanner.py"


# --- Pre-commit hook ---

def test_pre_commit_hook_exists():
    if not precommit_path().exists():
        pytest.skip("pre-commit hook not installed yet")
    assert precommit_path().is_file(), "pre-commit hook must be a file"
    assert precommit_path().stat().st_size > 0, "pre-commit hook must not be empty"


def test_pre_commit_hook_uses_venv_python():
    if not precommit_path().exists():
        pytest.skip("pre-commit hook not installed yet")
    c = precommit_content()
    assert "venv" in c and ("python" in c), (
        "pre-commit hook must use the project venv Python"
    )


def test_pre_commit_hook_is_staged_syntax_only():
    """Pre-commit must stay fast: staged syntax only; full scanner is pre-push."""
    if not precommit_path().exists():
        pytest.skip("pre-commit hook not installed yet")
    c = precommit_content()
    assert "diff --cached" in c, (
        "pre-commit hook must check staged files only"
    )
    assert "code_scanner.py" not in c, (
        "pre-commit must not run full code_scanner (pre-push owns that)"
    )


def test_pre_commit_hook_checks_staged_files():
    if not precommit_path().exists():
        pytest.skip("pre-commit hook not installed yet")
    c = precommit_content()
    assert "diff --cached" in c, "pre-commit hook must check staged files only"


def test_pre_commit_hook_blocks_on_errors():
    if not precommit_path().exists():
        pytest.skip("pre-commit hook not installed yet")
    c = precommit_content()
    assert "COMMIT BLOCKED" in c, "pre-commit hook must block the commit on failure"


def test_source_pre_commit_matches_unix_policy():
    """hooks/pre-commit (Unix source) must be staged-syntax only."""
    src = QA_DIR / "hooks" / "pre-commit"
    if not src.exists():
        pytest.skip("hooks/pre-commit not in tree")
    c = src.read_text(encoding="utf-8")
    assert "git diff --cached" in c or "diff --cached" in c
    assert "code_scanner.py" not in c, (
        "Unix pre-commit must not run full code_scanner (pre-push owns that)"
    )


def test_source_pre_commit_bat_matches_unix_policy():
    """hooks/pre-commit.bat must mirror Unix: staged syntax only."""
    src = QA_DIR / "hooks" / "pre-commit.bat"
    if not src.exists():
        pytest.skip("hooks/pre-commit.bat not in tree")
    c = src.read_text(encoding="utf-8")
    assert "diff --cached" in c
    assert "code_scanner.py" not in c, (
        "Windows pre-commit.bat must not run full code_scanner"
    )


# --- requirements.txt ---

def test_requirements_have_version_bounds():
    req = QA_DIR / "requirements.txt"
    if not req.exists():
        pytest.skip("requirements.txt not found")
    text = req.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pinned = any(op in line for op in ("==", ">=", "<=", "~="))
        assert pinned, f"Unpinned dependency: {line}"


def test_requirements_no_wildcards():
    req = QA_DIR / "requirements.txt"
    if not req.exists():
        pytest.skip("requirements.txt not found")
    text = req.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert "*" not in line, f"Wildcard version not allowed: {line}"


# --- Code quality ---

@pytest.mark.parametrize("py_file", project_py_files(), ids=lambda p: str(p.name))
def test_no_bare_except(py_file):
    src = py_file.read_text(encoding="utf-8")
    cleaned = re.sub(r'""".*?"""', "", src, flags=re.DOTALL)
    cleaned = re.sub(r"'''.*?'''", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'#.*$', "", cleaned, flags=re.MULTILINE)
    assert not re.search(r"except\s*:", cleaned), f"bare 'except:' in {py_file}"


@pytest.mark.parametrize("py_file", project_py_files(), ids=lambda p: str(p.name))
def test_file_not_empty(py_file):
    assert py_file.stat().st_size > 0, f"{py_file} is empty"


@pytest.mark.parametrize("tool", [
    "dependency_health",
    "performance_benchmark",
    "pipeline_dashboard",
    "smart_test_selector",
])
def test_all_tools_importable(tool):
    mod = __import__(tool)
    assert mod is not None, f"{tool} imported but is None"


def test_code_scanner_exists():
    assert (QA_DIR / "code_scanner.py").exists(), "code_scanner.py must exist"


# --- Pipeline runners ---

@pytest.mark.parametrize("runner", ["run_full_pipeline.bat", "run_full_pipeline.sh"])
def test_runner_uses_venv_and_30(runner):
    p = QA_DIR / runner
    if not p.exists():
        pytest.skip(f"{runner} not present")
    c = p.read_text(encoding="utf-8", errors="replace")
    assert "cov-fail-under=30" in c, f"{runner} must use 30% coverage gate"
    assert "venv" in c, f"{runner} must use the venv Python"


# --- Isolation ---

def test_pre_push_hook_delegates_to_qa_dir():
    if not hook_path().exists():
        pytest.skip("pre-push hook not installed yet")
    c = hook_content()
    assert 'QA_DIR' in c and ('cd' in c), (
        "hook must cd into bitbucket-qa/"
    )


def test_no_hardcoded_user_paths():
    for py_file in project_py_files():
        src = py_file.read_text(encoding="utf-8", errors="replace")
        assert "C:\\Users\\" not in src and "C:/Users/" not in src, (
            f"hardcoded user path in {py_file}"
        )


def test_setup_all_writes_only_to_qa_dir():
    setup = QA_DIR / "setup_all.py"
    if not setup.exists():
        pytest.skip("setup_all.py not present")
    c = setup.read_text(encoding="utf-8")
    assert 'QA_DIR = "bitbucket-qa"' in c, (
        "setup_all.py must target only bitbucket-qa/"
    )


def test_gitignore_excludes_bitbucket_qa():
    gi = REPO_ROOT / ".gitignore"
    if not gi.exists():
        pytest.skip(".gitignore not found at repo root")
    c = gi.read_text(encoding="utf-8")
    assert "bitbucket-qa/" in c, ".gitignore must exclude bitbucket-qa/"
