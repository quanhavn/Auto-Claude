#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for Auto Claude.
#
# Prepares both halves of the monorepo:
#   - apps/backend  : Python 3.12 venv + runtime and test dependencies
#   - apps/frontend : Electron/React node_modules (native modules rebuilt for Electron)
#
# Safe to run repeatedly: it converges on the same state and never starts a
# long-running process (no dev servers here). The desktop app is launched on
# demand during development, not from install.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# 1) Ensure Python 3.12 venv support (ensurepip) exists. Cursor's default image
#    ships python3.12 but not the python3.12-venv package that provides ensurepip.
if ! python3.12 -c "import ensurepip" >/dev/null 2>&1; then
  echo "==> Installing python3.12-venv (provides ensurepip)"
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3.12-venv python3.12-dev
fi

# 2) Backend: (re)create the virtualenv and install runtime dependencies.
echo "==> Installing backend dependencies"
npm run install:backend

# 3) Backend: install the test toolchain (pytest et al.) into the same venv.
echo "==> Installing backend test dependencies"
apps/backend/.venv/bin/pip install -q -r tests/requirements-test.txt

# 4) Frontend: install node dependencies. The postinstall step runs
#    electron-rebuild to compile native modules (node-pty) against Electron.
echo "==> Installing frontend dependencies"
npm run install:frontend

echo "==> Auto Claude environment ready"
