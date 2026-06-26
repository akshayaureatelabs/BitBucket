#!/bin/bash
cd "."
echo "Starting cross-platform setup..."
echo ""
python3 setup_all.py "$@" 2>/dev/null || python setup_all.py "$@"
