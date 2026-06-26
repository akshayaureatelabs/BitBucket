import os
import ast
import pytest

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_python_files():
    """Get all Python files excluding venv, .venv, and cache"""
    python_files = []
    exclude_dirs = {'venv', '.venv', '__pycache__', '.pytest_cache', '.git', 'tests'}
    
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py') and file not in ['test_precheck.py', 'dependency_health.py', 'performance_benchmark.py']:
                python_files.append(os.path.join(root, file))
    return python_files

@pytest.mark.parametrize("file_path", get_python_files())
def test_python_syntax(file_path):
    """Ensure all Python files have valid syntax"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    try:
        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"Syntax error in {file_path}: {e}")

def test_no_empty_python_files():
    """Ensure no empty Python files exist"""
    for file_path in get_python_files():
        assert os.path.getsize(file_path) > 0, f"{file_path} is empty"

def test_requirements_exists():
    """Ensure requirements.txt exists"""
    assert os.path.exists('requirements.txt'), "requirements.txt not found"

def test_pipeline_yml_exists():
    """Ensure bitbucket-pipelines.yml exists"""
    assert os.path.exists('bitbucket-pipelines.yml'), "bitbucket-pipelines.yml not found"