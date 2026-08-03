"""Regression tests for code_scanner process exit codes (IS-0001).

ERROR severity findings must yield exit code 1 so hooks can block.
Clean projects must yield exit code 0.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCANNER = ROOT / "code_scanner.py"


@pytest.mark.skipif(not SCANNER.exists(), reason="code_scanner.py missing")
def test_scanner_exits_nonzero_on_syntax_error(tmp_path):
    """A broken .py file must make the scanner exit with code 1."""
    bad = tmp_path / "broken.py"
    bad.write_text("def nope(\n", encoding="utf-8")  # intentional SyntaxError

    result = subprocess.run(
        [sys.executable, str(SCANNER), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0, (
        "code_scanner must exit non-zero when ERROR findings exist; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


@pytest.mark.skipif(not SCANNER.exists(), reason="code_scanner.py missing")
def test_scanner_exits_zero_on_clean_file(tmp_path):
    """A valid .py file with no ERROR findings should exit 0."""
    good = tmp_path / "ok.py"
    good.write_text("x = 1\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCANNER), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        "code_scanner must exit 0 when there are no ERROR findings; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
