# BitBucket Pipeline QA & Utility Suite

A comprehensive collection of Python-based tools and CI/CD configurations designed to optimize, monitor, and validate BitBucket Pipelines.

## 🚀 Overview

This project provides a suite of utilities to enhance the development lifecycle:
- **Smart Test Selection:** Analyze code changes to run only relevant tests.
- **Performance Benchmarking:** Track and compare execution metrics.
- **Dependency Health:** Monitor and report on the status of project dependencies.
- **Automated Dashboard:** Generate visual reports of pipeline performance.
- **Security & Quality:** Integrated linting, type checking, and security scanning.

## 🛠️ Getting Started

### Prerequisites
- Python 3.10+
- `pip` (Python package installer)

### Installation

#### Windows
Run the setup batch script:
```batch
setup.bat
```

#### Linux/macOS
Run the setup shell script:
```bash
chmod +x setup.sh
./setup.sh
```

These scripts will create a virtual environment (`venv`) and install all required dependencies listed in `requirements.txt`.

## 🧪 Running Tests & Utilities

### 1. Pre-merge Validation
Run basic sanity tests:
```bash
pytest test_precheck.py -v
```

### 2. Smart Test Selector
Generate a test matrix based on changes:
```bash
python smart_test_selector.py --summary --generate-matrix
```

### 3. Performance Benchmark
Run benchmarks and generate a report:
```bash
python performance_benchmark.py --run-benchmarks --generate-report
```

### 4. Dependency Health Check
Check for outdated or vulnerable packages:
```bash
python dependency_health.py --check-all --generate-report
```

### 5. Pipeline Dashboard
Simulate and view the dashboard:
```bash
python pipeline_dashboard.py --simulate-data --generate-dashboard
```

## 📂 Project Structure

- `bitbucket-pipelines.yml`: CI/CD configuration.
- `requirements.txt`: Project dependencies.
- `smart_test_selector.py`: Impact analysis tool.
- `performance_benchmark.py`: Benchmarking utility.
- `dependency_health.py`: Dependency monitoring script.
- `pipeline_dashboard.py`: Dashboard generation tool.
- `setup.*` / `test_phase1.*`: Automation scripts for setup and testing.

## 🔧 Maintenance

If you encounter encoding issues (common when moving files between Windows and Linux), run the fix scripts:
- **Windows:** `fix_encoding.bat`
- **Linux:** `fix_encoding.sh`
