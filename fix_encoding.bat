@echo off
echo 🔧 Fixing encoding issues...

:: Fix performance_benchmark.py
powershell -Command "(gc performance_benchmark.py) -replace '<td>{func\[\\''memory\\''\]', '<td>{func.get(\\''avg_memory_mb\\'', 0)' | Out-File -encoding UTF8 performance_benchmark.py"

:: Fix dependency_health.py
powershell -Command "(gc dependency_health.py) -replace 'open\(self\.requirements_file, \\''r\\''\)', 'open(self.requirements_file, \\''r\\'', encoding=\\''utf-8\\'')' | Out-File -encoding UTF8 dependency_health.py"

:: Fix pipeline_dashboard.py
powershell -Command "(gc pipeline_dashboard.py) -replace 'open\(dashboard_file, \\''w\\''\)', 'open(dashboard_file, \\''w\\'', encoding=\\''utf-8\\'')' | Out-File -encoding UTF8 pipeline_dashboard.py"

echo ✅ Fixes applied! Run tests again.