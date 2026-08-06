#!/usr/bin/env python3
"""One-shot restore: download good versions from parent commit and fix isolation paths.

Run from repo root:
    python restore_broken_tools.py

Then commit the restored files:
    git add dependency_health.py performance_benchmark.py pipeline_dashboard.py
    git commit -m "fix: restore tools from PLACEHOLDER/LOADING; correct isolation paths"
    git push
"""
import urllib.request
from pathlib import Path

BASE = (
    "https://raw.githubusercontent.com/akshayaureatelabs/BitBucket/"
    "cb0aee85089ad8efe15ca2ad84a11d3b42e6aec6/"
)

FIXES = {
    "dependency_health.py": [
        (
            'self.base_dir / "bitbucket-qa" / "dependency-reports"',
            'self.base_dir / "dependency-reports"',
        ),
    ],
    "performance_benchmark.py": [
        (
            'self.base_dir / "bitbucket-qa" / ".benchmarks"',
            'self.base_dir / ".benchmarks"',
        ),
    ],
    "pipeline_dashboard.py": [
        (
            'self.base_dir / "bitbucket-qa" / "pipeline-metrics.db"',
            'self.base_dir / "pipeline-metrics.db"',
        ),
        (
            'self.base_dir / "bitbucket-qa" / "dashboard"',
            'self.base_dir / "dashboard"',
        ),
    ],
}


def main() -> None:
    for name, replacements in FIXES.items():
        url = BASE + name
        print(f"Fetching {name}...")
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read().decode("utf-8")
        for old, new in replacements:
            if old not in data:
                print(f"  WARN: pattern not found in {name}: {old[:50]}...")
            data = data.replace(old, new)
        Path(name).write_text(data, encoding="utf-8", newline="\n")
        print(f"  Wrote {name} ({len(data)} bytes)")

    print()
    print("Done. Next:")
    print("  git add dependency_health.py performance_benchmark.py pipeline_dashboard.py")
    print('  git commit -m "fix: restore tools; correct isolation paths"')
    print("  git push")
    print()
    print("Optional: refresh embeds + setup_all hooks/venv fixes:")
    print("  python _gen_setup.py")
    print("  # then re-apply setup_all write_qa_files/venv changes if needed")


if __name__ == "__main__":
    main()
