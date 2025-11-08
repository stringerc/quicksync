## Resonance Desktop Agent Packaging Plan

This folder documents how we build and distribute platform-specific binaries of the Resonance Agent.

### Build Pipeline (Automated)

1. **TypeScript Compile** – `npm run build` generates `dist/agent/index_secure.js`.
2. **Binary Packaging** – `npm run build:agent-binaries` invokes [`pkg`](https://github.com/vercel/pkg) to create self-contained executables for:
   - `node18-macos-x64`
   - `node18-linux-x64`
   - `node18-win-x64`
3. **Archives & hashes** – the script zips each binary, bundles documentation/config samples, and writes `manifest.json` + `update-manifest.json` (with SHA-256 checksums) into `dist-binaries/`.
4. **GitHub Actions** – `.github/workflows/build-agent-binaries.yml` runs on tag `agent-v*` (or manual dispatch), publishes archives, checksums, and manifests.

### Files & Scripts

| Path | Description |
|------|-------------|
| `scripts/build-agent-binaries.js` | Orchestrates compile, pkg packaging, zipping, checksum + update manifest generation. |
| `package.json > pkg` | Declares assets (policy defaults) and default targets. |
| `.github/workflows/build-agent-binaries.yml` | CI workflow producing artifacts on demand or tagged releases. |
| `dist-binaries/manifest.json` | Metadata for release automation (version, targets). |

### Next Steps (Manual / To Automate)

- **Code-signing:** integrate platform-specific signing (EV certificates for Windows, Apple notarisation, Linux package signatures). See `SIGNING_AND_INSTALLERS.md`.
- **Installers:** wrap binaries using WiX/MSIX (Windows), `pkgbuild`/`productbuild` (macOS), `fpm`/`nfpm` for `.deb`/`.rpm`. See `SIGNING_AND_INSTALLERS.md`.
- **Auto-update:** host `update-manifest.json`, and have agents poll it to download new archives (see `AUTO_UPDATE.md` for the wire protocol).
- **Config generation:** provide CLI (`resonance-agent register --license`) that writes encrypted credentials per OS.
- **Documentation:** publish OS-specific install/uninstall guides mapped to enterprise requirements (silent install flags, proxy support).

This plan follows best practices used by other telemetry agents (e.g., Datadog, New Relic) by shipping a minimal native wrapper that communicates with the Resonance cloud via TLS.

