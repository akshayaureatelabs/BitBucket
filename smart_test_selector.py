"""
Smart Test Selector - Only run tests affected by code changes
Phase 1 Feature: Test Impact Analysis
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import ast

class SmartTestSelector:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.cache_dir = self.base_dir / '.test-cache'
        self.cache_dir.mkdir(exist_ok=True)
        
        self.changed_files = self._get_changed_files()
        self.test_mapping = self._build_test_mapping()
    
    def _get_changed_files(self) -> List[str]:
        """Get files changed in PR or commit"""
        try:
            if os.environ.get('BITBUCKET_PR_ID'):
                dest_commit = os.environ.get('BITBUCKET_PR_DESTINATION_COMMIT', 'main')
                source_commit = os.environ.get('BITBUCKET_PR_SOURCE_COMMIT', 'HEAD')
                
                result = subprocess.run(
                    ['git', 'diff', '--name-only', f'{dest_commit}..{source_commit}'],
                    capture_output=True, text=True, cwd=self.base_dir
                )
                if result.returncode == 0:
                    return [f for f in result.stdout.split('\n') if f]
            
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                capture_output=True, text=True, cwd=self.base_dir
            )
            if result.returncode == 0:
                files = [f for f in result.stdout.split('\n') if f]
                
                result = subprocess.run(
                    ['git', 'ls-files', '--others', '--exclude-standard'],
                    capture_output=True, text=True, cwd=self.base_dir
                )
                if result.returncode == 0:
                    files.extend([f for f in result.stdout.split('\n') if f])
                return files
        except Exception as e:
            print(f"[WARN] Error getting changed files: {e}")
        return []
    
    def _build_test_mapping(self) -> Dict[str, List[str]]:
        """Build mapping between source files and test files"""
        mapping = {}
        tests_dir = self.base_dir / 'tests'
        if not tests_dir.exists():
            return mapping
        
        for test_file in tests_dir.rglob('test_*.py'):
            module_name = test_file.stem.replace('test_', '')
            source_patterns = [
                self.base_dir / f"{module_name}.py",
                self.base_dir / "src" / f"{module_name}.py",
                self.base_dir / "lib" / f"{module_name}.py",
            ]
            
            for source_path in source_patterns:
                if source_path.exists():
                    rel_source = str(source_path.relative_to(self.base_dir))
                    rel_test = str(test_file.relative_to(self.base_dir))
                    mapping.setdefault(rel_source, []).append(rel_test)
            
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and not node.module.startswith('tests'):
                            source_file = node.module.replace('.', '/') + '.py'
                            mapping.setdefault(source_file, [])
                            if str(test_file.relative_to(self.base_dir)) not in mapping[source_file]:
                                mapping[source_file].append(str(test_file.relative_to(self.base_dir)))
                    
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if not alias.name.startswith('tests'):
                                source_file = alias.name.replace('.', '/') + '.py'
                                mapping.setdefault(source_file, [])
                                if str(test_file.relative_to(self.base_dir)) not in mapping[source_file]:
                                    mapping[source_file].append(str(test_file.relative_to(self.base_dir)))
            except Exception as e:
                print(f"[WARN] Error parsing {test_file}: {e}")
        
        return mapping
    
    def get_affected_tests(self) -> Set[str]:
        """Get set of tests affected by changed files"""
        affected = set()
        
        for file_path in self.changed_files:
            if file_path.startswith('tests/') and file_path.endswith('.py'):
                affected.add(file_path)
            
            if file_path in self.test_mapping:
                affected.update(self.test_mapping[file_path])
            
            if file_path in ['requirements.txt', 'setup.py', 'conftest.py']:
                tests_dir = self.base_dir / 'tests'
                if tests_dir.exists():
                    for test_file in tests_dir.rglob('test_*.py'):
                        affected.add(str(test_file.relative_to(self.base_dir)))
                break
        
        return affected
    
    def get_test_hash(self, test_files: List[str]) -> str:
        """Generate hash of test files for caching"""
        hasher = hashlib.md5()
        for test_file in sorted(test_files):
            file_path = self.base_dir / test_file
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        return hasher.hexdigest()
    
    def should_run_tests(self, test_files: List[str]) -> bool:
        """Check if tests need to run based on cache"""
        if not test_files:
            return False
        
        cache_file = self.cache_dir / 'last_test_hash.txt'
        current_hash = self.get_test_hash(test_files)
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                if f.read().strip() == current_hash:
                    return False
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(current_hash)
        return True
    
    def generate_test_matrix(self) -> Dict:
        """Generate test matrix for parallel execution"""
        affected_tests = list(self.get_affected_tests())
        
        if not affected_tests:
            smoke_tests = []
            tests_dir = self.base_dir / 'tests'
            if tests_dir.exists():
                for test_file in tests_dir.rglob('test_smoke_*.py'):
                    smoke_tests.append(str(test_file.relative_to(self.base_dir)))
            
            if smoke_tests:
                return {"tests": smoke_tests, "reason": "Running smoke tests only", "timestamp": datetime.now().isoformat()}
            else:
                all_tests = []
                for test_file in tests_dir.rglob('test_*.py'):
                    all_tests.append(str(test_file.relative_to(self.base_dir)))
                return {"tests": all_tests, "reason": "No affected tests identified, running all", "timestamp": datetime.now().isoformat()}
        
        if not self.should_run_tests(affected_tests):
            return {"tests": [], "reason": "Tests haven't changed since last run", "timestamp": datetime.now().isoformat()}
        
        return {
            "tests": affected_tests,
            "reason": f"Affected by changes in: {', '.join(self.changed_files[:5])}",
            "timestamp": datetime.now().isoformat(),
            "parallel_groups": self._group_tests(affected_tests)
        }
    
    def _group_tests(self, tests: List[str], num_groups: int = 4) -> Dict:
        """Group tests for balanced parallel execution"""
        groups = {f"group_{i}": [] for i in range(num_groups)}
        for i, test_file in enumerate(sorted(tests)):
            groups[f"group_{i % num_groups}"].append(test_file)
        return groups
    
    def print_summary(self):
        """Print summary of analysis"""
        print("\n" + "="*60)
        print("SMART TEST SELECTOR - SUMMARY")
        print("="*60)
        print(f"\nChanged Files ({len(self.changed_files)}):")
        for file in self.changed_files[:10]:
            print(f"   • {file}")
        print(f"\nTest Mapping ({len(self.test_mapping)} source files mapped):")
        for source, tests in list(self.test_mapping.items())[:5]:
            print(f"   • {source} -> {len(tests)} tests")
        affected = self.get_affected_tests()
        print(f"\nAffected Tests: {len(affected)}")
        for test in list(affected)[:10]:
            print(f"   • {test}")
        print("\n" + "="*60)

def main():
    parser = argparse.ArgumentParser(description="Smart Test Selector")
    parser.add_argument("--generate-matrix", action="store_true", help="Generate test matrix JSON")
    parser.add_argument("--summary", action="store_true", help="Print analysis summary")
    parser.add_argument("--output", "-o", default="test-matrix.json", help="Output file for test matrix")
    
    args = parser.parse_args()
    selector = SmartTestSelector()
    
    if args.summary:
        selector.print_summary()
    
    if args.generate_matrix:
        matrix = selector.generate_test_matrix()
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(matrix, f, indent=2)
        print(f"Test matrix saved to {args.output}")
        if not matrix['tests']:
            print("No tests need to run at this time")
            sys.exit(0)

if __name__ == "__main__":
    main()