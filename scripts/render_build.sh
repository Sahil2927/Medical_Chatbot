#!/usr/bin/env bash
set -euo pipefail

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing CPU-only PyTorch (smaller/faster on Render)"
python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

echo "==> Installing Python dependencies"
python -m pip install --no-cache-dir -r requirements.txt

echo "==> Building MediAssist frontend"
cd frontend
npm install
npm run build

echo "==> Render build complete"
