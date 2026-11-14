#!/usr/bin/env bash
set -e

echo "=== Installing rock.ai (Autonomous 24/7 Multi-Agent Fleet) ==="

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required. Please install Python 3.10+ and re-run."
    exit 1
fi

python3 -m pip install --upgrade pip
pip install -e .

echo "=== rock.ai installed successfully! ==="
echo "Run 'rock onboard' to configure your agent fleet."
