<#
.SYNOPSIS
  Builds a signed Windows installer (MSI/MSIX) for the Resonance Agent.

.DESCRIPTION
  This script wraps the packaged binary located in ../dist-binaries/resonance-agent-windows-x64.exe
  into an MSI installer using WiX Toolset. Signing requires an Authenticode certificate.

.REQUIREMENTS
  - WiX Toolset (candle.exe, light.exe) on the PATH
  - signtool.exe from Windows SDK
  - Environment variables:
      $env:RESONANCE_AGENT_VERSION         (optional override)
      $env:RESONANCE_SIGN_CERT_PATH        (PFX/P12 certificate path)
      $env:RESONANCE_SIGN_CERT_PASSWORD    (certificate password, optional if not needed)
      $env:RESONANCE_INSTALL_DIR           (defaults to "C:\Program Files\Resonance")
#>

param(
  [string]$Version = $env:RESONANCE_AGENT_VERSION,
  [string]$BinaryPath = "..\dist-binaries\resonance-agent-windows-x64.exe",
  [string]$OutputDir = "..\dist-installers",
  [string]$InstallDir = $(if ($env:RESONANCE_INSTALL_DIR) { $env:RESONANCE_INSTALL_DIR } else { "C:\Program Files\Resonance" })
)

if (-not (Test-Path $BinaryPath)) {
  Write-Error "Packaged binary not found at $BinaryPath. Run npm run build:agent-binaries first."
  exit 1
}

if (-not $Version) {
  $packageJson = Get-Content "..\package.json" | ConvertFrom-Json
  $Version = $packageJson.version
}

$Version = $Version -replace '^v', ''
$OutputDir = Resolve-Path $OutputDir
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$wxsTemplate = @"
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="Resonance Agent" Language="1033" Version="$Version" Manufacturer="Resonance" UpgradeCode="E1F6C4E2-0000-4000-A001-RES0NANC3">
    <Package InstallerVersion="510" Compressed="yes" InstallScope="perMachine" Description="Resonance Agent"/>
    <MajorUpgrade Schedule="afterInstallValidate" DowngradeErrorMessage="A newer version of Resonance Agent is already installed." />
    <MediaTemplate EmbedCab="yes"/>

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLDIR" Name="Resonance">
          <Component Id="AgentBinary" Guid="*" Win64="yes">
            <File Id="ResonanceAgentExe" Name="resonance-agent.exe" Source="$(var.AgentBinary)" KeyPath="yes"/>
          </Component>
        </Directory>
      </Directory>
    </Directory>

    <Feature Id="MainFeature" Title="Resonance Agent" Level="1">
      <ComponentRef Id="AgentBinary"/>
    </Feature>
  </Product>
</Wix>
"@

$tmpDir = New-Item -ItemType Directory -Path (Join-Path ([System.IO.Path]::GetTempPath()) "resonance-wix") -Force
$wxsPath = Join-Path $tmpDir "resonance-agent.wxs"
$wxsTemplate | Out-File -Encoding UTF8 $wxsPath

$env:AgentBinary = (Resolve-Path $BinaryPath)

Write-Host "Running WiX candle.exe"
candle.exe $wxsPath -dAgentBinary="$env:AgentBinary" -out (Join-Path $tmpDir "resonance-agent.wixobj") | Out-Null

Write-Host "Running WiX light.exe"
light.exe (Join-Path $tmpDir "resonance-agent.wixobj") -o (Join-Path $OutputDir "ResonanceAgent-$Version.msi") | Out-Null

$msiPath = Join-Path $OutputDir "ResonanceAgent-$Version.msi"

if ($env:RESONANCE_SIGN_CERT_PATH) {
  Write-Host "Signing MSI..."
  $signArgs = @("sign", "/fd", "SHA256", "/tr", "http://timestamp.digicert.com", "/td", "SHA256", "/f", $env:RESONANCE_SIGN_CERT_PATH)
  if ($env:RESONANCE_SIGN_CERT_PASSWORD) {
    $signArgs += @("/p", $env:RESONANCE_SIGN_CERT_PASSWORD)
  }
  $signArgs += $msiPath
  & signtool.exe @signArgs
}

Write-Host "Windows installer created at $msiPath"
Write-Host "Remember to sign the packaged binary itself if distributing separately."

