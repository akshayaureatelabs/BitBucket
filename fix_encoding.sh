echo "🔧 Fixing encoding issues on Linux/Unix..."

# Fix Python files with encoding issues using sed
# Note: These regex patterns mirror the logic in fix_encoding.bat

# Fix performance_benchmark.py
if [ -f "performance_benchmark.py" ]; then
    sed -i "s/<td>{func\['memory'\]}/<td>{func.get('avg_memory_mb', 0)}/g" performance_benchmark.py
    # Add encoding='utf-8' if missing in open() calls
    sed -i "s/open(\([^,]*\), 'w')/open(\1, 'w', encoding='utf-8')/g" performance_benchmark.py
    echo "✅ Fixed performance_benchmark.py"
fi

# Fix dependency_health.py
if [ -f "dependency_health.py" ]; then
    sed -i "s/open(self.requirements_file, 'r')/open(self.requirements_file, 'r', encoding='utf-8')/g" dependency_health.py
    echo "✅ Fixed dependency_health.py"
fi

# Fix pipeline_dashboard.py
if [ -f "pipeline_dashboard.py" ]; then
    sed -i "s/open(dashboard_file, 'w')/open(dashboard_file, 'w', encoding='utf-8')/g" pipeline_dashboard.py
    echo "✅ Fixed pipeline_dashboard.py"
fi

echo "✅ All fixes applied! Run tests again."