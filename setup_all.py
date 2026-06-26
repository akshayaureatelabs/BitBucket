"""
Cross-platform setup script for BitBucket QA Suite.
Works on Windows, Linux, and macOS.

Usage:
    python setup_all.py          # Full setup
    python setup_all.py --skip-tests   # Skip test validation
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path


# Colors for output (works on most modern terminals)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @staticmethod
    def disable():
        Colors.GREEN = Colors.RED = Colors.YELLOW = Colors.CYAN = Colors.BOLD = Colors.END = ''


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 50}")
    print(f"  {text}")
    print(f"{'=' * 50}{Colors.END}\n")


def print_step(step, total, text):
    print(f"{Colors.BOLD}[{step}/{total}]{Colors.END} {text}")


def print_ok(text):
    print(f"  {Colors.GREEN}OK{Colors.END} {text}")


def print_error(text):
    print(f"  {Colors.RED}ERROR{Colors.END} {text}")


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result. cmd is a list (no shell=True)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=300
        )
        if check and result.returncode != 0:
            stderr = result.stderr.strip()[:200]
            print(f"  {Colors.RED}FAILED{Colors.END}: {stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  {Colors.RED}TIMEOUT{Colors.END}: Command took too long")
        return False
    except FileNotFoundError:
        print(f"  {Colors.RED}NOT FOUND{Colors.END}: {cmd[0]}")
        return False
    except Exception as e:
        print(f"  {Colors.RED}ERROR{Colors.END}: {e}")
        return False


def get_python_command():
    """Get the correct Python command for the platform."""
    # Prioritize based on platform
    if sys.platform == 'win32':
        candidates = ['python', 'python3']
    else:
        candidates = ['python3', 'python']

    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, '--version'], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version_str = result.stdout.strip()
                parts = version_str.split('.')
                if len(parts) >= 2:
                    major = int(parts[0].replace('Python ', ''))
                    minor = int(parts[1])
                    if major >= 3 and minor >= 11:
                        return cmd
                    else:
                        print(f"  {Colors.YELLOW}WARNING{Colors.END}: Found {version_str}, need 3.11+")
        except (FileNotFoundError, ValueError):
            continue
    return None


def get_venv_python(project_dir):
    """Get the path to the venv Python executable."""
    if sys.platform == 'win32':
        return str(project_dir / 'venv' / 'Scripts' / 'python.exe')
    else:
        return str(project_dir / 'venv' / 'bin' / 'python')


def setup(skip_tests=False):
    project_dir = Path(__file__).parent.resolve()
    total_steps = 4

    print_header("BitBucket QA Suite - One-Click Setup")
    print(f"  Platform: {sys.platform}")
    print(f"  Python:   {sys.version}")
    print(f"  Directory: {project_dir}\n")

    # Step 1: Check Python
    print_step(1, total_steps, "Checking Python...")
    python_cmd = get_python_command()
    if not python_cmd:
        print_error("Python 3.11+ not found!")
        print("  Please install Python 3.11 or newer:")
        print("  https://www.python.org/downloads/")
        return False
    print_ok(f"Found {python_cmd}")

    # Step 2: Create virtual environment
    print_step(2, total_steps, "Setting up virtual environment...")
    venv_dir = project_dir / 'venv'
    venv_python = get_venv_python(project_dir)

    # Check if existing venv is usable (has python AND pip)
    venv_usable = False
    if venv_dir.exists() and Path(venv_python).exists():
        pip_check = subprocess.run(
            [venv_python, '-m', 'pip', '--version'],
            capture_output=True, text=True, timeout=10
        )
        venv_usable = pip_check.returncode == 0

        if not venv_usable:
            # Try to recover pip via ensurepip (handles locked venv scenario)
            print(f"  Venv exists but pip is missing, recovering via ensurepip...")
            ensure_result = subprocess.run(
                [venv_python, '-m', 'ensurepip', '--upgrade'],
                capture_output=True, text=True, timeout=60
            )
            if ensure_result.returncode == 0:
                venv_usable = True
                print(f"  Pip recovered successfully")

    if venv_usable:
        print(f"  Existing venv found, reusing...")
    else:
        if venv_dir.exists():
            print(f"  Removing broken venv...")
            try:
                shutil.rmtree(venv_dir)
            except PermissionError:
                print_error("Cannot delete locked venv. Please close all Python processes and try again.")
                return False

        result = subprocess.run(
            [python_cmd, '-m', 'venv', str(venv_dir)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print_error(f"Failed to create venv: {result.stderr}")
            return False

        # Verify new venv is usable
        pip_check = subprocess.run(
            [venv_python, '-m', 'pip', '--version'],
            capture_output=True, text=True, timeout=10
        )
        if pip_check.returncode != 0:
            print_error("Venv created but pip is missing!")
            return False

    print_ok("Virtual environment ready")

    # Step 3: Install dependencies
    # Use 'python -m pip' instead of calling pip directly — more reliable across platforms
    print_step(3, total_steps, "Installing dependencies...")
    pip_cmd = [venv_python, '-m', 'pip']

    if not run_command(pip_cmd + ['install', '--upgrade', 'pip'], cwd=str(project_dir)):
        print_error("Failed to upgrade pip")
        return False

    if not run_command(pip_cmd + ['install', '-r', 'requirements.txt'], cwd=str(project_dir)):
        print_error("Failed to install dependencies")
        return False
    print_ok("All dependencies installed")

    # Step 4: Validate
    if skip_tests:
        print_step(4, total_steps, "Skipping validation (--skip-tests)")
    else:
        print_step(4, total_steps, "Running validation tests...")
        test_result = subprocess.run(
            [venv_python, '-m', 'pytest', 'test_precheck.py', 'tests/', '-v', '--tb=short'],
            cwd=str(project_dir), timeout=120
        )
        if test_result.returncode != 0:
            print_error("Some tests failed! Check output above.")
            return False

        # Verify tools
        print(f"\n  Verifying tools...")
        tools = [
            ("dependency_health", "from dependency_health import DependencyHealthCheck; c = DependencyHealthCheck(); pkgs = c._parse_requirements(); print(f'  dependency_health: OK ({len(pkgs)} packages)')"),
            ("pipeline_dashboard", "from pipeline_dashboard import PipelineDashboard; d = PipelineDashboard(); print('  pipeline_dashboard: OK')"),
            ("performance_benchmark", "from performance_benchmark import PerformanceBenchmark; b = PerformanceBenchmark(); print('  performance_benchmark: OK')"),
            ("smart_test_selector", "from smart_test_selector import SmartTestSelector; print('  smart_test_selector: OK')"),
        ]
        all_ok = True
        for name, code in tools:
            result = subprocess.run(
                [venv_python, '-c', code],
                cwd=str(project_dir), capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print_ok(result.stdout.strip())
            else:
                print_error(f"{name}: {result.stderr.strip()[:100]}")
                all_ok = False

        if not all_ok:
            print_error("Some tools failed verification!")
            return False

    # Done
    print_header("Setup Complete!")
    print("  Available commands:")
    print(f"    {Colors.CYAN}pytest test_precheck.py -v{Colors.END}        Run precheck tests")
    print(f"    {Colors.CYAN}pytest tests/ -v{Colors.END}                  Run all tests")
    print(f"    {Colors.CYAN}python smart_test_selector.py{Colors.END}     Smart test selection")
    print(f"    {Colors.CYAN}python performance_benchmark.py{Colors.END}   Run benchmarks")
    print(f"    {Colors.CYAN}python dependency_health.py{Colors.END}       Check dependencies")
    print(f"    {Colors.CYAN}python pipeline_dashboard.py{Colors.END}      Generate dashboard")
    print()
    return True


def main():
    # Enable ANSI colors on Windows 10+
    if sys.platform == 'win32':
        os.system('')
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            Colors.disable()

    parser = argparse.ArgumentParser(description="BitBucket QA Suite - Cross-platform Setup")
    parser.add_argument("--skip-tests", action="store_true", help="Skip test validation after setup")
    args = parser.parse_args()

    success = setup(skip_tests=args.skip_tests)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
