#!/bin/bash
cd "$(dirname "$0")"
echo "Starting cross-platform setup..."
echo ""
python3 setup_all.py "$@" || python setup_all.py "$@"
