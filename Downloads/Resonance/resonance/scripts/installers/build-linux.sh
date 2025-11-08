#!/usr/bin/env bash
# Build .deb and .rpm packages for the Resonance Agent using fpm.
#
# Requirements:
#   - Ruby + fpm (gem install fpm)
#   - Resonance agent binaries produced by npm run build:agent-binaries
#   - GPG key (optional) for signing repositories / packages
#
# Environment variables:
#   RESONANCE_AGENT_VERSION
#   RESONANCE_AGENT_BINARY=../dist-binaries/resonance-agent-linux-x64
#   RESONANCE_INSTALL_DIR=/usr/local/bin
#   RESONANCE_MAINTAINER="Resonance <support@resonance>"
#   RESONANCE_DESCRIPTION="Resonance Agent"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_BINARIES="${ROOT_DIR}/dist-binaries"
OUTPUT_DIR="${ROOT_DIR}/dist-installers"
PAYLOAD_DIR="$(mktemp -d)"

AGENT_BINARY="${RESONANCE_AGENT_BINARY:-${DIST_BINARIES}/resonance-agent-linux-x64}"
VERSION="${RESONANCE_AGENT_VERSION:-$(node -pe "require('${ROOT_DIR}/package.json').version")}"
INSTALL_DIR="${RESONANCE_INSTALL_DIR:-/usr/local/bin}"
MAINTAINER="${RESONANCE_MAINTAINER:-Resonance <support@resonance>}"
DESCRIPTION="${RESONANCE_DESCRIPTION:-Resonance Agent}"
ARCH="${RESONANCE_ARCHITECTURE:-amd64}"

if [[ ! -f "${AGENT_BINARY}" ]]; then
  echo "Packaged binary not found at ${AGENT_BINARY}. Run npm run build:agent-binaries first." >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"
mkdir -p "${PAYLOAD_DIR}${INSTALL_DIR}"

cp "${AGENT_BINARY}" "${PAYLOAD_DIR}${INSTALL_DIR}/resonance-agent"
chmod 755 "${PAYLOAD_DIR}${INSTALL_DIR}/resonance-agent"

echo "Building .deb..."
fpm -s dir -t deb \
  -n resonance-agent \
  -v "${VERSION}" \
  --description "${DESCRIPTION}" \
  --maintainer "${MAINTAINER}" \
  --architecture "${ARCH}" \
  --prefix / \
  --rpm-os linux \
  --deb-no-default-config-files \
  --after-install "${ROOT_DIR}/docs/desktop-agent/postinstall.sh" \
  --after-remove "${ROOT_DIR}/docs/desktop-agent/postremove.sh" \
  --package "${OUTPUT_DIR}/resonance-agent_${VERSION}_${ARCH}.deb" \
  "${PAYLOAD_DIR}${INSTALL_DIR}=/usr/local/bin"

echo "Building .rpm..."
fpm -s dir -t rpm \
  -n resonance-agent \
  -v "${VERSION}" \
  --description "${DESCRIPTION}" \
  --maintainer "${MAINTAINER}" \
  --architecture "${ARCH}" \
  --prefix / \
  --rpm-os linux \
  --after-install "${ROOT_DIR}/docs/desktop-agent/postinstall.sh" \
  --after-remove "${ROOT_DIR}/docs/desktop-agent/postremove.sh" \
  --package "${OUTPUT_DIR}/resonance-agent-${VERSION}-${ARCH}.rpm" \
  "${PAYLOAD_DIR}${INSTALL_DIR}=/usr/local/bin"

echo "Linux packages generated in ${OUTPUT_DIR}"
rm -rf "${PAYLOAD_DIR}"

