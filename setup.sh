#!/bin/bash
cd "$(dirname "$0")"
echo "Starting cross-platform setup..."
echo ""
python3 setup_all.py "$@" || python setup_all.py "$@"
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Setup failed! Check the output above."
fi
