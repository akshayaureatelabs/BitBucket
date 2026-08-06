"""Regenerate setup_all.py with embedded base64-encoded QA files.

Usage: python _gen_setup.py
Run from the bitbucket-qa project root directory.

This script only updates the EMBEDDED_FILES section in setup_all.py.
All other code in setup_all.py is left untouched.
"""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
setup_path = ROOT / "setup_all.py"

sources = {
    "requirements.txt": "requirements.txt",
    "requirements.lock": "requirements.lock",
    ".gitignore": "qa_gitignore_template.txt",
    "code_scanner.py": "code_scanner.py",
    "test_precheck.py": "test_precheck.py",
    "tests/__init__.py": "tests/__init__.py",
    "tests/test_sample.py": "tests/test_sample.py",
    "tests/test_fixes.py": "tests/test_fixes.py",
    "tests/test_quality_gate.py": "tests/test_quality_gate.py",
    "tests/test_scanner_exit.py": "tests/test_scanner_exit.py",
    "tests/test_tools_units.py": "tests/test_tools_units.py",
    "dependency_health.py": "dependency_health.py",
    "performance_benchmark.py": "performance_benchmark.py",
    "pipeline_dashboard.py": "pipeline_dashboard.py",
    "smart_test_selector.py": "smart_test_selector.py",
    "run_full_pipeline.bat": "run_full_pipeline.bat",
    "run_full_pipeline.sh": "run_full_pipeline.sh",
    "bitbucket-pipelines.yml": "bitbucket-pipelines.yml",
    ".git/hooks/pre-push": "hooks/pre-push",
    ".git/hooks/pre-push.bat": "hooks/pre-push.bat",
    ".git/hooks/pre-commit": "hooks/pre-commit",
    ".git/hooks/pre-commit.bat": "hooks/pre-commit.bat",
}

lines = []
for key, src in sources.items():
    p = ROOT / src
    data = p.read_bytes() if p.exists() else b""
    b64 = base64.b64encode(data).decode()
    lines.append('    "%s": "%s",' % (key, b64))

new_dict = "EMBEDDED_FILES = {\n" + "\n".join(lines) + "\n}\n"

src_text = setup_path.read_text(encoding="utf-8")

start = src_text.index("EMBEDDED_FILES = {")
rest = src_text[start:]

# Find matching closing brace by counting nesting
brace_count = 0
end_pos = 0
for i, ch in enumerate(rest):
    if ch == "{":
        brace_count += 1
    elif ch == "}":
        brace_count -= 1
        if brace_count == 0:
            # Find end of line after closing brace
            end_pos = rest.index("\n", i) + 1 if "\n" in rest[i:] else i + 1
            break

end = start + end_pos
new_src = src_text[:start] + new_dict + src_text[end:]

setup_path.write_text(new_src, encoding="utf-8", newline="\n")
print("setup_all.py regenerated - EMBEDDED_FILES updated with latest source files")
