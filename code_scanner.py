"""
Project Code Scanner — Real issue detection, not style fluff.

Scans .py, .ts, .js, .tsx, .jsx files for:

  PYTHON:
    - Syntax errors (ast.parse)
    - Unused imports
    - Bare except clauses

  TYPESCRIPT / JAVASCRIPT:
    - Broken local imports (file doesn't exist)
    - Duplicate function names across files
    - Duplicate Express routes
    - Undefined route handlers
    - console.log in production code

  BOTH:
    - Empty files
    - Missing newline at end of file

Output format:
  [PASS] or [FAIL] per file
  Each issue:  ~ L{line}: {message}  (Fix: {suggestion})
"""

import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------

class Issue:
    def __init__(self, file, line, severity, message, fix=""):
        self.file = file
        self.line = line
        self.severity = severity  # ERROR | WARNING
        self.message = message
        self.fix = fix

    def __str__(self):
        fix_part = f"  (Fix: {self.fix})" if self.fix else ""
        return f"{self.file}:{self.line}: {self.severity}: {self.message}{fix_part}"


class ScanResult:
    def __init__(self):
        self.files_scanned = 0
        self.issues = []
        self.errors = 0
        self.warnings = 0

    @property
    def passed(self):
        return self.errors == 0

    def summary(self):
        total = self.errors + self.warnings
        if total == 0:
            return f"All {self.files_scanned} files clean - 0 issues"
        parts = []
        if self.errors:
            parts.append(f"{self.errors} error(s)")
        if self.warnings:
            parts.append(f"{self.warnings} warning(s)")
        return f"{self.files_scanned} files scanned, {total} issue(s): {', '.join(parts)}"


# ------------------------------------------------------------------
# Scanner
# ------------------------------------------------------------------

class CodeScanner:
    """Scans a project directory for real code issues."""

    EXCLUDE_DIRS = {
        "venv", ".venv", "__pycache__", "__pypackages__",
        ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache",
        "node_modules", "dist", "build", ".next", ".nuxt",
        "htmlcov", "coverage", "dashboard",
        "dependency-reports", "test-results", "bitbucket-qa",
        ".tox", ".eggs", "*.egg-info", "out", "vendor",
    }

    JS_EXTENSIONS = {".ts", ".js", ".tsx", ".jsx"}

    # Regex patterns
    IMPORT_RE = re.compile(
        r'import\s+(.*?)\s+from\s+[\'"](.*?)[\'"]'
    )
    EXPORT_RE = re.compile(
        r'export\s+(?:default\s+)?(?:class|function|const|let|var)?\s*([A-Za-z0-9_]+)?'
    )
    FUNCTION_RE = re.compile(
        r'function\s+([A-Za-z0-9_]+)'
    )
    ARROW_RE = re.compile(
        r'const\s+([A-Za-z0-9_]+)\s*=\s*(?:\(|async\s*\()'
    )
    ROUTE_RE = re.compile(
        r'app\.(use|get|post|put|delete|patch)\s*\(\s*[\'"](.*?)[\'"]\s*,\s*([A-Za-z0-9_]+)'
    )

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------

    def scan(self) -> ScanResult:
        result = ScanResult()

        py_files = self._collect(".py")
        js_files = self._collect(*self.JS_EXTENSIONS)
        all_files = py_files + js_files
        result.files_scanned = len(all_files)

        # --- Per-file checks ---
        for f in py_files:
            result.issues.extend(self._scan_python(f))
        for f in js_files:
            result.issues.extend(self._scan_js(f))

        # --- Cross-file checks (JS/TS only) ---
        result.issues.extend(self._check_broken_imports(js_files))
        result.issues.extend(self._check_duplicate_functions(js_files))
        result.issues.extend(self._check_duplicate_routes(js_files))
        result.issues.extend(self._check_route_handlers(js_files))

        # Tally
        for issue in result.issues:
            if issue.severity == "ERROR":
                result.errors += 1
            else:
                result.warnings += 1

        return result

    # ------------------------------------------------------------------
    # File collection
    # ------------------------------------------------------------------

    def _collect(self, *extensions) -> list:
        files = []
        for root, dirs, filenames in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            for fn in filenames:
                if fn.endswith(extensions):
                    files.append(Path(root) / fn)
        return sorted(files)

    def _rel(self, filepath: Path) -> str:
        try:
            return str(filepath.relative_to(self.project_root))
        except ValueError:
            return str(filepath)

    def _read(self, filepath: Path) -> str:
        try:
            return filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Python per-file checks
    # ------------------------------------------------------------------

    def _scan_python(self, filepath: Path) -> list:
        issues = []
        rel = self._rel(filepath)
        source = self._read(filepath)

        if not source.strip():
            issues.append(Issue(rel, 0, "ERROR", "File is empty"))
            return issues

        # Syntax check
        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError as e:
            issues.append(Issue(rel, e.lineno or 0, "ERROR",
                                f"Syntax error: {e.msg}"))
            return issues

        # Unused imports
        imported = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    name = alias.asname or alias.name
                    imported[name] = (node.lineno, f"{mod}.{alias.name}")

        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                n = node
                while isinstance(n, ast.Attribute):
                    n = n.value
                if isinstance(n, ast.Name):
                    used.add(n.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                used.add(node.name)

        for name, (lineno, module) in imported.items():
            if name not in used and name != "__all__":
                issues.append(Issue(rel, lineno, "WARNING",
                                    f"Unused import: '{name}' from {module}"))

        # Bare except
        cleaned = re.sub(r'""".*?"""', '', source, flags=re.DOTALL)
        cleaned = re.sub(r"'''.*?'''", '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'"[^"]*"', '""', cleaned)
        cleaned = re.sub(r"'[^']*'", "''", cleaned)
        cleaned = re.sub(r'#.*$', '', cleaned, flags=re.MULTILINE)
        for i, line in enumerate(cleaned.splitlines(), 1):
            if re.search(r'except\s*:', line):
                issues.append(Issue(rel, i, "WARNING",
                                    "Bare except clause — use 'except Exception:'"))

        # Missing newline
        if source and not source.endswith("\n"):
            issues.append(Issue(rel, len(source.splitlines()), "WARNING",
                                "No newline at end of file"))

        return issues

    # ------------------------------------------------------------------
    # JavaScript/TypeScript per-file checks
    # ------------------------------------------------------------------

    def _scan_js(self, filepath: Path) -> list:
        issues = []
        rel = self._rel(filepath)
        source = self._read(filepath)

        if not source.strip():
            issues.append(Issue(rel, 0, "ERROR", "File is empty"))
            return issues

        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.rstrip("\n\r")

            # Trailing whitespace
            if stripped != stripped.rstrip():
                issues.append(Issue(rel, i, "WARNING", "Trailing whitespace"))

            # console.log in non-test files
            if "console.log" in stripped and "test" not in filepath.name.lower():
                code_part = stripped.split("//")[0]
                if "console.log" in code_part:
                    issues.append(Issue(rel, i, "WARNING",
                                        "console.log in production code",
                                        "Remove or replace with logger"))

        # Missing newline
        if source and not source.endswith("\n"):
            issues.append(Issue(rel, len(lines), "WARNING",
                                "No newline at end of file"))

        return issues

    # ------------------------------------------------------------------
    # Cross-file: Broken local imports
    # ------------------------------------------------------------------

    def _check_broken_imports(self, js_files: list) -> list:
        issues = []
        for filepath in js_files:
            rel = self._rel(filepath)
            source = self._read(filepath)

            for m in self.IMPORT_RE.finditer(source):
                module = m.group(2)
                if not module.startswith("."):
                    continue  # skip npm packages

                lineno = source[:m.start()].count("\n") + 1
                resolved = self._resolve_import(filepath, module)

                if not resolved:
                    issues.append(Issue(
                        rel, lineno, "ERROR",
                        f"Broken import: '{module}' — file not found",
                        "Check path or create the missing file"
                    ))
        return issues

    def _resolve_import(self, base_file: Path, module: str) -> bool:
        p = (base_file.parent / module).resolve()
        base = str(p)
        candidates = [
            base,
            base + ".ts", base + ".tsx", base + ".js", base + ".jsx",
            re.sub(r"\.js$", ".ts", base),
            re.sub(r"\.js$", ".tsx", base),
            re.sub(r"\.jsx$", ".tsx", base),
            os.path.join(base, "index.ts"),
            os.path.join(base, "index.tsx"),
            os.path.join(base, "index.js"),
            os.path.join(base, "index.jsx"),
        ]
        return any(Path(c).exists() for c in candidates)

    # ------------------------------------------------------------------
    # Cross-file: Duplicate functions
    # ------------------------------------------------------------------

    def _check_duplicate_functions(self, js_files: list) -> list:
        issues = []
        fn_map = defaultdict(list)  # name -> [(file, line)]

        for filepath in js_files:
            rel = self._rel(filepath)
            source = self._read(filepath)

            for m in self.FUNCTION_RE.finditer(source):
                name = m.group(1)
                line = source[:m.start()].count("\n") + 1
                fn_map[name].append((rel, line))

            for m in self.ARROW_RE.finditer(source):
                name = m.group(1)
                line = source[:m.start()].count("\n") + 1
                fn_map[name].append((rel, line))

        for name, locations in fn_map.items():
            if len(locations) > 1:
                for file, line in locations:
                    others = [f for f, _ in locations if f != file]
                    issues.append(Issue(
                        file, line, "WARNING",
                        f"Duplicate function '{name}' defined in {len(locations)} files",
                        f"Also in: {', '.join(others)}"
                    ))
        return issues

    # ------------------------------------------------------------------
    # Cross-file: Duplicate routes
    # ------------------------------------------------------------------

    def _check_duplicate_routes(self, js_files: list) -> list:
        issues = []
        route_map = defaultdict(list)  # path -> [(file, line, handler)]

        for filepath in js_files:
            rel = self._rel(filepath)
            source = self._read(filepath)

            for m in self.ROUTE_RE.finditer(source):
                path = m.group(2)
                handler = m.group(3)
                line = source[:m.start()].count("\n") + 1
                route_map[path].append((rel, line, handler))

        for path, locations in route_map.items():
            if len(locations) > 1:
                for file, line, handler in locations:
                    issues.append(Issue(
                        file, line, "WARNING",
                        f"Duplicate route '{path}' — registered {len(locations)} times",
                        f"Also in: {', '.join(f for f, _, _ in locations if f != file)}"
                    ))
        return issues

    # ------------------------------------------------------------------
    # Cross-file: Undefined route handlers
    # ------------------------------------------------------------------

    def _check_route_handlers(self, js_files: list) -> list:
        issues = []

        for filepath in js_files:
            rel = self._rel(filepath)
            source = self._read(filepath)

            # Find route handlers
            handlers = []
            for m in self.ROUTE_RE.finditer(source):
                line = source[:m.start()].count("\n") + 1
                handlers.append((m.group(3), line))

            if not handlers:
                continue

            # Collect declared names (imports + local declarations)
            declared = set()

            for m in self.IMPORT_RE.finditer(source):
                left = m.group(1)
                for name in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", left):
                    declared.add(name)

            for m in re.finditer(
                r"(?:const|let|var|function|class)\s+([A-Za-z_][A-Za-z0-9_]*)",
                source
            ):
                declared.add(m.group(1))

            # Check each handler is declared
            for handler, line in handlers:
                if handler not in declared:
                    # Try to suggest a similar name
                    suggestion = ""
                    for name in declared:
                        if handler.lower() in name.lower() or name.lower() in handler.lower():
                            suggestion = f"Did you mean '{name}'?"
                            break

                    issues.append(Issue(
                        rel, line, "ERROR",
                        f"Undefined route handler '{handler}'",
                        suggestion or "Import or declare this handler"
                    ))
        return issues


# ------------------------------------------------------------------
# Output formatting
# ------------------------------------------------------------------

def format_result(result: ScanResult) -> str:
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("  PROJECT CODE SCAN")
    lines.append("=" * 70)
    lines.append("")

    by_file = defaultdict(list)
    for issue in result.issues:
        by_file[issue.file].append(issue)

    if not by_file:
        lines.append(f"  {result.summary()}")
        lines.append("")
        return "\n".join(lines)

    for filepath in sorted(by_file.keys()):
        file_issues = by_file[filepath]
        has_error = any(i.severity == "ERROR" for i in file_issues)
        status = "FAIL" if has_error else "PASS"
        lines.append(f"  [{status}] {filepath}")

        for issue in file_issues:
            marker = "!" if issue.severity == "ERROR" else "~"
            fix_part = f"  -> {issue.fix}" if issue.fix else ""
            lines.append(f"    {marker} L{issue.line}: {issue.message}{fix_part}")
        lines.append("")

    lines.append("-" * 70)
    lines.append(f"  {result.summary()}")
    if result.errors > 0:
        lines.append(f"  RESULT: BLOCKED — {result.errors} error(s) must be fixed")
    else:
        lines.append(f"  RESULT: PASSED")
    lines.append("-" * 70)
    lines.append("")

    return "\n".join(lines)


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scan project code for real issues")
    parser.add_argument("directory", nargs="?", default=".",
                        help="Project root to scan")
    args = parser.parse_args()

    scanner = CodeScanner(args.directory)
    result = scanner.scan()
    output = format_result(result)

    # Always save full output to bitbucket-qa/output.txt
    output_dir = Path(args.directory) / "bitbucket-qa"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "output.txt"
    output_file.write_text(output, encoding="utf-8")

    # Print summary + redirect note to terminal
    print(output)
    print(f"  For full output, refer to: {output_file}")
    print()
    sys.exit(1 if result.errors > 0 else 0)


if __name__ == "__main__":
    main()
