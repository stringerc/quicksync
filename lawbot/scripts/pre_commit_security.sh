#!/usr/bin/env bash
# Invoked by pre-commit from the *git* root. Delegates to security_scan.sh next to this file.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/security_scan.sh"
