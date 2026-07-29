"""
Smart Test Selector - Only run tests affected by code changes
Phase 1 Feature: Test Impact Analysis

Author: Sr. QA Tester - Akshaykumar Dudhwala

Usage:
    python smart_test_selector.py --summary
    python smart_test_selector.py --generate-matrix --output matrix.json
    python smart_test_selector.py --generate-matrix --base-branch develop

Environment:
    BITBUCKET_PR_ID              - Triggers PR diff mode
    BITBUCKET_PR_SOURCE_COMMIT   - Source commit hash
    BITBUCKET_PR_DESTINATION_COMMIT - Target commit hash

Architecture:
    _get_changed_files()  -> git diff detection (unstaged + staged + base branch)
    _build_test_mapping() -> AST import analysis + naming convention + comment hints
    get_affected_tests()  -> cross-reference changed files with mapping
    generate_test_matrix() -> output for CI parallel pipeline
    should_run_tests()    -> content-hash based cache gate (source + test files)

Cache: .test-cache/ (auto-created)
"""

import argparse
import ast
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class SmartTestSelector:
    def __init__(self, base_branch=None):
        self.base_dir = Path(__file__).parent
        self.cache_dir = self.base_dir / ".test-cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.base_branch = base_branch

        self.changed_files = self._get_changed_files()
        self.changed_lines = self._get_changed_lines()
        self.test_mapping = self._build_test_mapping()

    @staticmethod
    def _normalize_path(path) -> str:
        """Normalize path to forward slashes for cross-platform consistency"""
        return Path(path).as_posix()

    def _get_changed_files(self) -> List[str]:
        """Get files changed in PR or commit (unstaged + staged + base branch)"""
        try:
            if os.environ.get("BITBUCKET_PR_ID"):
                dest_commit = os.environ.get("BITBUCKET_PR_DESTINATION_COMMIT", "main")
                source_commit = os.environ.get("BITBUCKET_PR_SOURCE_COMMIT", "HEAD")

                result = subprocess.run(
                    ["git", "diff", "--name-only", f"{dest_commit}..{source_commit}"],
                    capture_output=True,
                    text=True,
                    cwd=self.base_dir,
                )
                if result.returncode == 0:
                    return [self._normalize_path(f) for f in result.stdout.split("\n") if f]

            files = set()

            # Unstaged changes
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            if result.returncode == 0:
                files.update(self._normalize_path(f) for f in result.stdout.split("\n") if f)

            # Staged changes
            result = subprocess.run(
                ["git", "diff", "--staged", "--name-only"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            if result.returncode == 0:
                files.update(self._normalize_path(f) for f in result.stdout.split("\n") if f)

            # Diff against base branch (for CI/local comparison)
            if self.base_branch:
                merge_base = self._get_merge_base(self.base_branch)
                if merge_base:
                    result = subprocess.run(
                        ["git", "diff", "--name-only", merge_base, "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=self.base_dir,
                    )
                    if result.returncode == 0:
                        files.update(self._normalize_path(f) for f in result.stdout.split("\n") if f)
            else:
                # Auto-detect: prefer tracked upstream branch, then fallback
                upstream = self._get_upstream_branch()
                branches = [upstream] if upstream else []
                branches.extend(["main", "develop", "master"])

                for branch in branches:
                    if not branch:
                        continue
                    merge_base = self._get_merge_base(branch)
                    if merge_base:
                        result = subprocess.run(
                            ["git", "diff", "--name-only", merge_base, "HEAD"],
                            capture_output=True,
                            text=True,
                            cwd=self.base_dir,
                        )
                        if result.returncode == 0:
                            files.update(self._normalize_path(f) for f in result.stdout.split("\n") if f)
                        break

            # Untracked files
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            if result.returncode == 0:
                files.update(self._normalize_path(f) for f in result.stdout.split("\n") if f)

            return list(files)
        except Exception as e:
            logger.warning("Error getting changed files: %s", e)
        return []

    def _get_upstream_branch(self) -> str:
        """Get the tracking upstream branch (e.g. origin/main, origin/develop)"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD@{upstream}"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            if result.returncode == 0:
                upstream = result.stdout.strip()
                if upstream:
                    return upstream
        except Exception:
            pass
        return None

    def _get_merge_base(self, branch: str) -> str:
        """Get merge base commit between current HEAD and a branch"""
        try:
            # Try the branch name directly (git resolves tracking refs)
            result = subprocess.run(
                ["git", "merge-base", branch, "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            if result.returncode == 0:
                return result.stdout.strip()

            # Fallback: try with origin/ prefix
            result = subprocess.run(
                ["git", "merge-base", f"origin/{branch}", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _get_changed_lines(self) -> Dict[str, List[int]]:
        """Get line-level changes per file for granularity (unstaged + staged)"""
        changed_lines = {}
        try:
            # Unstaged + staged combined via HEAD
            result = subprocess.run(
                ["git", "diff", "HEAD", "--unified=0"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self.base_dir,
            )
            if result.returncode != 0:
                return changed_lines

            current_file = None
            for line in result.stdout.split("\n"):
                if line.startswith("+++ b/"):
                    current_file = self._normalize_path(line[6:])
                elif line.startswith("@@") and current_file:
                    match = re.search(r"\+(\d+)", line)
                    if match:
                        start = int(match.group(1))
                        changed_lines.setdefault(current_file, []).append(start)
        except Exception as e:
            logger.debug("Error getting changed lines: %s", e)
        return changed_lines

    def _get_changed_functions(self, file_path: str) -> Set[str]:
        """Extract function/class names that contain changed lines"""
        functions = set()
        if file_path not in self.changed_lines:
            return functions

        full_path = self.base_dir / file_path
        if not full_path.exists():
            return functions

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            tree = ast.parse("".join(lines))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                        changed_in_range = any(
                            node.lineno <= ln <= node.end_lineno
                            for ln in self.changed_lines.get(file_path, [])
                        )
                        if changed_in_range:
                            functions.add(node.name)
        except (SyntaxError, Exception):
            pass
        return functions

    def _parse_comment_hints(self, test_file: Path) -> List[str]:
        """Parse '# test-depends: src/foo.py, src/bar.py' comments from test files"""
        dependencies = []
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                for line in f:
                    match = re.search(r"#\s*test-depends:\s*(.+)", line)
                    if match:
                        for dep in match.group(1).split(","):
                            dep = dep.strip()
                            if dep:
                                dependencies.append(self._normalize_path(dep))
        except Exception:
            pass
        return dependencies

    def _build_test_mapping(self) -> Dict[str, List[str]]:
        """Build mapping between source files and test files"""
        mapping = {}
        tests_dir = self.base_dir / "tests"
        if not tests_dir.exists():
            return mapping

        for test_file in tests_dir.rglob("test_*.py"):
            # Method 1: Naming convention (test_fixes.py -> fixes.py)
            module_name = test_file.stem.replace("test_", "")
            source_patterns = [
                self.base_dir / f"{module_name}.py",
                self.base_dir / "src" / f"{module_name}.py",
                self.base_dir / "lib" / f"{module_name}.py",
            ]

            rel_test = self._normalize_path(test_file.relative_to(self.base_dir))

            for source_path in source_patterns:
                if source_path.exists():
                    rel_source = self._normalize_path(source_path.relative_to(self.base_dir))
                    mapping.setdefault(rel_source, [])
                    if rel_test not in mapping[rel_source]:
                        mapping[rel_source].append(rel_test)

            # Method 2: AST import analysis
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and not node.module.startswith("tests"):
                            source_file = self._normalize_path(node.module.replace(".", "/") + ".py")
                            mapping.setdefault(source_file, [])
                            if rel_test not in mapping[source_file]:
                                mapping[source_file].append(rel_test)

                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if not alias.name.startswith("tests"):
                                source_file = self._normalize_path(alias.name.replace(".", "/") + ".py")
                                mapping.setdefault(source_file, [])
                                if rel_test not in mapping[source_file]:
                                    mapping[source_file].append(rel_test)

            except SyntaxError as e:
                logger.warning("Syntax error in %s — skipping: %s", test_file, e)
            except Exception as e:
                logger.warning("Error parsing %s: %s", test_file, e)

            # Method 3: Comment-based hints
            for dep in self._parse_comment_hints(test_file):
                mapping.setdefault(dep, [])
                if rel_test not in mapping[dep]:
                    mapping[dep].append(rel_test)

        return mapping

    def get_affected_tests(self) -> Set[str]:
        """Get set of tests affected by changed files"""
        affected = set()

        for file_path in self.changed_files:
            # Direct test file changes (normalize both sides)
            if file_path.startswith("tests/") and file_path.endswith(".py"):
                affected.add(file_path)

            # Mapping lookup
            if file_path in self.test_mapping:
                affected.update(self.test_mapping[file_path])

            # Log changed functions for visibility
            changed_funcs = self._get_changed_functions(file_path)
            if changed_funcs:
                logger.debug("Functions changed in %s: %s", file_path, changed_funcs)

            # Infrastructure changes trigger all tests
            if file_path in ["requirements.txt", "setup.py", "conftest.py"]:
                tests_dir = self.base_dir / "tests"
                if tests_dir.exists():
                    for test_file in tests_dir.rglob("test_*.py"):
                        affected.add(self._normalize_path(test_file.relative_to(self.base_dir)))
                break

        return affected

    def get_test_hash(self, test_files: List[str]) -> str:
        """Generate hash of source + test files for caching"""
        hasher = hashlib.sha256()

        # Hash changed source files
        for file_path in sorted(self.changed_files):
            fp = self.base_dir / file_path
            if fp.exists():
                with open(fp, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        hasher.update(chunk)

        # Hash test files
        for test_file in sorted(test_files):
            file_path = self.base_dir / test_file
            if file_path.exists():
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        hasher.update(chunk)
        return hasher.hexdigest()

    def should_run_tests(self, test_files: List[str]) -> bool:
        """Check if tests need to run based on cache"""
        if not test_files:
            return False

        cache_file = self.cache_dir / "last_test_hash.txt"
        current_hash = self.get_test_hash(test_files)

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                if f.read().strip() == current_hash:
                    return False

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(current_hash)
        return True

    def generate_test_matrix(self) -> Dict:
        """Generate test matrix for parallel execution"""
        affected_tests = list(self.get_affected_tests())

        if not affected_tests:
            smoke_tests = []
            tests_dir = self.base_dir / "tests"
            if tests_dir.exists():
                for test_file in tests_dir.rglob("test_smoke_*.py"):
                    smoke_tests.append(self._normalize_path(test_file.relative_to(self.base_dir)))

            if smoke_tests:
                return {
                    "tests": smoke_tests,
                    "reason": "Running smoke tests only",
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                all_tests = []
                if tests_dir.exists():
                    for test_file in tests_dir.rglob("test_*.py"):
                        all_tests.append(self._normalize_path(test_file.relative_to(self.base_dir)))
                return {
                    "tests": all_tests,
                    "reason": "No affected tests identified, running all",
                    "timestamp": datetime.now().isoformat(),
                }

        if not self.should_run_tests(affected_tests):
            return {
                "tests": [],
                "reason": "Tests haven't changed since last run",
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "tests": affected_tests,
            "reason": f"Affected by changes in: {', '.join(self.changed_files[:5])}",
            "timestamp": datetime.now().isoformat(),
            "parallel_groups": self._group_tests(affected_tests),
        }

    def _group_tests(self, tests: List[str], num_groups: int = 4) -> Dict:
        """Group tests for balanced parallel execution using timing data"""
        timing = self._load_timing_cache()
        sorted_tests = sorted(tests, key=lambda t: timing.get(t, 1.0), reverse=True)

        groups = {f"group_{i}": {"tests": [], "estimated_seconds": 0.0} for i in range(num_groups)}
        for test in sorted_tests:
            lightest = min(groups, key=lambda g: groups[g]["estimated_seconds"])
            groups[lightest]["tests"].append(test)
            groups[lightest]["estimated_seconds"] += timing.get(test, 1.0)

        # Flatten for backward compatibility
        return {k: v["tests"] for k, v in groups.items()}

    def _load_timing_cache(self) -> Dict[str, float]:
        """Load test execution timing from cache"""
        timing_file = self.cache_dir / "timing.json"
        if timing_file.exists():
            try:
                with open(timing_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_timing_cache(self, test_name: str, duration: float):
        """Save test execution timing"""
        timing = self._load_timing_cache()
        timing[test_name] = duration
        timing_file = self.cache_dir / "timing.json"
        with open(timing_file, "w", encoding="utf-8") as f:
            json.dump(timing, f, indent=2)

    def print_summary(self):
        """Print summary of analysis"""
        logger.info("\n" + "=" * 60)
        logger.info("SMART TEST SELECTOR - SUMMARY")
        logger.info("=" * 60)
        logger.info("Changed Files (%d):", len(self.changed_files))
        for file in self.changed_files[:10]:
            logger.info("   - %s", file)
        logger.info("Test Mapping (%d source files mapped):", len(self.test_mapping))
        for source, tests in list(self.test_mapping.items())[:5]:
            logger.info("   - %s -> %d tests", source, len(tests))
        affected = self.get_affected_tests()
        logger.info("Affected Tests: %d", len(affected))
        for test in list(affected)[:10]:
            logger.info("   - %s", test)
        logger.info("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Smart Test Selector")
    parser.add_argument(
        "--generate-matrix", action="store_true", help="Generate test matrix JSON"
    )
    parser.add_argument("--summary", action="store_true", help="Print analysis summary")
    parser.add_argument(
        "--output", "-o", default="test-matrix.json", help="Output file for test matrix"
    )
    parser.add_argument(
        "--base-branch", default=None,
        help="Base branch to diff against (default: auto-detect main/develop/master)"
    )

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parser.parse_args()
    selector = SmartTestSelector(base_branch=args.base_branch)

    if args.summary:
        selector.print_summary()

    if args.generate_matrix:
        matrix = selector.generate_test_matrix()
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(matrix, f, indent=2)
        logger.info("Test matrix saved to %s", args.output)
        if not matrix["tests"]:
            logger.info("No tests need to run at this time")
            sys.exit(0)


if __name__ == "__main__":
    main()
