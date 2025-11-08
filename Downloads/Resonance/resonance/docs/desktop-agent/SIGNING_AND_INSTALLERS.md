## Code Signing & Installer Automation

Delivering the Resonance Agent to enterprise customers requires signed binaries and OS-specific installers. This guide summarises the steps, with references to vendor documentation.

### 1. Certificates

| Platform | Requirement | References |
|----------|-------------|-----------|
| **Windows** | Extended Validation (EV) Authenticode certificate to avoid SmartScreen warnings. | [Microsoft Code Signing Guide](https://learn.microsoft.com/windows/security/application-security/code-signing/) |
| **macOS** | Apple Developer ID certificate (Application + Installer) and notarisation token. | [Apple Notarization Docs](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution) |
| **Linux** | GPG key for repository metadata; optional RPM/DEB signing. | [Debian Secure APT](https://wiki.debian.org/SecureApt), [RPM Signing](https://docs.fedoraproject.org/en-US/quick-docs/creating-rpm-packages/#chap-Preparing_GPG-keys) |

Store signing credentials in your secrets manager (GitHub Actions OIDC + Azure Key Vault/AWS KMS, or self-hosted runner with HSM access).

### 2. Windows (.msi / .exe)

1. Use **WiX Toolset** or **Advanced Installer** to wrap `resonance-agent-windows-x64.exe` into an MSI.
   ```powershell
   # Example WiX candle/light pipeline (simplified)
   candle.exe resonance-agent.wxs -out build/
   light.exe build/resonance-agent.wixobj -ext WixUIExtension -out dist-binaries/resonance-agent.msi
   ```
2. Sign the MSI + binary with `signtool.exe`:
   ```powershell
   signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 /f %CERT_PATH% dist-binaries\resonance-agent-windows-x64.exe
   signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 /f %CERT_PATH% dist-binaries\resonance-agent.msi
   ```
3. Optional: generate an MSIX package for Windows Store distribution (`MakeAppx.exe`, `SignTool.exe`).

### 3. macOS (.pkg)

1. Create a component package using `pkgbuild`:
   ```bash
   pkgbuild \
     --root payload/ \
     --identifier com.resonance.agent \
     --version "$AGENT_VERSION" \
     --install-location /usr/local/bin \
     dist-binaries/ResonanceAgent.pkg
   ```
2. Sign with the Installer certificate:
   ```bash
   productsign \
     --sign "Developer ID Installer: Your Company (TEAMID)" \
     dist-binaries/ResonanceAgent.pkg \
     dist-binaries/ResonanceAgent-signed.pkg
   ```
3. Notarise via Apple:
   ```bash
   xcrun notarytool submit dist-binaries/ResonanceAgent-signed.pkg --apple-id "$APPLE_ID" --team-id "$TEAM_ID" --password "@keychain:AC_PASSWORD" --wait
   xcrun stapler staple dist-binaries/ResonanceAgent-signed.pkg
   ```

### 4. Linux (.deb / .rpm / tar.gz)

Use [`fpm`](https://github.com/jordansissel/fpm) or [`nfpm`](https://github.com/goreleaser/nfpm):

```bash
fpm -s dir -t deb \
  -n resonance-agent \
  -v "$AGENT_VERSION" \
  --description "Resonance Agent" \
  --architecture amd64 \
  --prefix /usr/local/bin \
  resonance-agent-linux-x64
```

Sign repositories with your GPG key (`reprepro`, `createrepo_c` + `gpg --detach-sign`).

### 5. Automation Hooks

1. **GitHub Actions or CI**:
   - Use matrix jobs with OS-specific runners (Windows/macOS self-hosted or GitHub-hosted).
   - Fetch signing certs from a secure store. Example: Azure Key Vault + `signtool` for Windows.
2. **Environment variables**:
   - `WIN_SIGN_CERT_PATH`, `WIN_SIGN_CERT_PASSWORD`
   - `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_AC_PASSWORD`
   - `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`
3. **Post-build**: upload MSI/PKG/DEB/RPM + zipped binaries and update-manifest to release buckets (S3/CloudFront, Azure Blob, etc.).

### 6. Installer Features (Recommended)

- Install as a system service (`sc create` on Windows, `launchctl` on macOS, `systemd` unit on Linux).
- Prompt for license/API key (or read from command-line flag `/quiet LICENSE_KEY=...` for unattended installs).
- Include uninstall scripts and log locations.

### 7. QA Checklist

- ✅ Smoke test: install/uninstall on each platform.
- ✅ Verify signatures (e.g., `signtool verify`, `spctl --assess`, `dpkg --info`).
- ✅ Check Gatekeeper/SmartScreen prompts suppressed.
- ✅ Ensure installers deploy updated `policy-defaults.json` and respect config overrides.
- ✅ Validate auto-start and log output.

