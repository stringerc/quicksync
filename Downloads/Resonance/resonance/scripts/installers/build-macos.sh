#!/usr/bin/env bash
# Build a signed macOS pkg for the Resonance Agent.
# Requires:
#   - Xcode command line tools
#   - Apple Developer ID Application & Installer certificates
#   - Logged-in notarisation credentials (`xcrun notarytool store-credentials`)
#
# Environment variables (override defaults as needed):
#   RESONANCE_AGENT_VERSION
#   RESONANCE_AGENT_BINARY=../dist-binaries/resonance-agent-macos-x64
#   RESONANCE_INSTALL_DIR=/usr/local/bin
#   RESONANCE_PKG_ID=com.resonance.agent
#   RESONANCE_PKG_SIGN_ID="Developer ID Installer: Example (TEAMID)"
#   RESONANCE_APPLE_TEAM_ID=TEAMID
#   RESONANCE_NOTARY_PROFILE=ResonanceNotary

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_BINARIES="${ROOT_DIR}/dist-binaries"
OUTPUT_DIR="${ROOT_DIR}/dist-installers"
PAYLOAD_DIR="$(mktemp -d)"

AGENT_BINARY="${RESONANCE_AGENT_BINARY:-${DIST_BINARIES}/resonance-agent-macos-x64}"
VERSION="${RESONANCE_AGENT_VERSION:-$(node -pe "require('${ROOT_DIR}/package.json').version")}"
INSTALL_DIR="${RESONANCE_INSTALL_DIR:-/usr/local/bin}"
PKG_ID="${RESONANCE_PKG_ID:-com.resonance.agent}"
PKG_SIGN_ID="${RESONANCE_PKG_SIGN_ID:-""}"
TEAM_ID="${RESONANCE_APPLE_TEAM_ID:-""}"
NOTARY_PROFILE="${RESONANCE_NOTARY_PROFILE:-ResonanceNotary}"

if [[ ! -f "${AGENT_BINARY}" ]]; then
  echo "Packaged binary not found at ${AGENT_BINARY}. Run npm run build:agent-binaries first." >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"
mkdir -p "${PAYLOAD_DIR}${INSTALL_DIR}"

cp "${AGENT_BINARY}" "${PAYLOAD_DIR}${INSTALL_DIR}/resonance-agent"
chmod 755 "${PAYLOAD_DIR}${INSTALL_DIR}/resonance-agent"

PKG_UNSIGNED="${OUTPUT_DIR}/ResonanceAgent-${VERSION}.pkg"
PKG_SIGNED="${OUTPUT_DIR}/ResonanceAgent-${VERSION}-signed.pkg"

echo "Building pkg..."
pkgbuild \
  --root "${PAYLOAD_DIR}" \
  --identifier "${PKG_ID}" \
  --version "${VERSION}" \
  --install-location "${INSTALL_DIR}" \
  "${PKG_UNSIGNED}"

if [[ -n "${PKG_SIGN_ID}" ]]; then
  echo "Signing pkg..."
  productsign --sign "${PKG_SIGN_ID}" "${PKG_UNSIGNED}" "${PKG_SIGNED}"
else
  cp "${PKG_UNSIGNED}" "${PKG_SIGNED}"
fi

if [[ -n "${TEAM_ID}" ]]; then
  echo "Submitting for notarisation..."
  xcrun notarytool submit "${PKG_SIGNED}" --keychain-profile "${NOTARY_PROFILE}" --team-id "${TEAM_ID}" --wait
  echo "Stapling ticket..."
  xcrun stapler staple "${PKG_SIGNED}"
fi

echo "macOS installer available at ${PKG_SIGNED}"
echo "Cleanup..."
rm -rf "${PAYLOAD_DIR}"

