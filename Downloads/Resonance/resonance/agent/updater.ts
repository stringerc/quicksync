import * as fs from 'fs';
import { createWriteStream } from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as crypto from 'crypto';
import { pipeline } from 'stream/promises';
import AdmZip from 'adm-zip';

interface UpdateAsset {
  os: 'macos' | 'linux' | 'windows';
  arch: 'x64' | 'arm64' | string;
  file: string;
  checksum: string;
  downloadUrl: string;
}

interface UpdateManifest {
  version: string;
  publishedAt?: string;
  notes?: string;
  assets: UpdateAsset[];
}

interface AutoUpdateOptions {
  manifestUrl?: string;
  intervalMs?: number;
  stagingDir?: string;
}

interface InstallResult {
  installed: boolean;
  message?: string;
}

const PROJECT_ROOT = path.resolve(__dirname, '..');
const processWithPkg = process as NodeJS.Process & { pkg?: unknown };
const EXEC_DIR = processWithPkg.pkg ? path.dirname(process.execPath) : PROJECT_ROOT;
const DEFAULT_STAGING_DIR = path.join(EXEC_DIR, 'updates');
const CURRENT_VERSION =
  process.env.RESONANCE_AGENT_VERSION ||
  (() => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      return require('../../package.json').version as string;
    } catch {
      return '0.0.0';
    }
  })();

const MIN_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
const DEFAULT_INTERVAL_MS = 6 * 60 * 60 * 1000; // 6 hours

let updateTimer: NodeJS.Timeout | null = null;

function ensureDir(dir: string) {
  fs.mkdirSync(dir, { recursive: true });
}

function compareVersions(a: string, b: string): number {
  const toParts = (v: string) => v.split('.').map((part) => parseInt(part, 10) || 0);
  const aParts = toParts(a);
  const bParts = toParts(b);
  const maxLen = Math.max(aParts.length, bParts.length);
  for (let i = 0; i < maxLen; i += 1) {
    const diff = (aParts[i] || 0) - (bParts[i] || 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

function getPlatformDescriptor(): { os: UpdateAsset['os']; arch: UpdateAsset['arch'] } | null {
  switch (process.platform) {
    case 'darwin':
      return { os: 'macos', arch: process.arch === 'arm64' ? 'arm64' : 'x64' };
    case 'linux':
      return { os: 'linux', arch: process.arch as UpdateAsset['arch'] };
    case 'win32':
      return { os: 'windows', arch: process.arch === 'arm64' ? 'arm64' : 'x64' };
    default:
      return null;
  }
}

async function fetchManifest(manifestUrl: string): Promise<UpdateManifest> {
  const response = await fetch(manifestUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch update manifest: HTTP ${response.status}`);
  }
  return response.json() as Promise<UpdateManifest>;
}

async function downloadAsset(url: string, destination: string) {
  const response = await fetch(url);
  if (!response.ok || !response.body) {
    throw new Error(`Failed to download update asset: HTTP ${response.status}`);
  }

  await pipeline(response.body, createWriteStream(destination));
}

function verifyChecksum(filePath: string, expectedChecksum: string) {
  const [algo, hashValue] = expectedChecksum.split(':');
  if (!algo || !hashValue) {
    throw new Error(`Invalid checksum format: ${expectedChecksum}`);
  }

  const hash = crypto.createHash(algo);
  hash.update(fs.readFileSync(filePath));
  const digest = hash.digest('hex');
  if (digest.toLowerCase() !== hashValue.toLowerCase()) {
    throw new Error(`Checksum mismatch. Expected ${hashValue}, got ${digest}`);
  }
}

function determineStagingDir(customDir?: string) {
  if (customDir) return customDir;
  return DEFAULT_STAGING_DIR;
}

function findBinaryInArchive(zip: AdmZip, expectsExe: boolean): AdmZip.IZipEntry | undefined {
  const entries = zip.getEntries().filter((entry) => !entry.isDirectory);
  const matcher = (entry: AdmZip.IZipEntry) => {
    const normalized = entry.entryName.replace(/\\/g, '/');
    const isExe = normalized.toLowerCase().endsWith('.exe');
    const looksLikeBinary = normalized.includes('resonance-agent');
    return looksLikeBinary && (!!expectsExe === isExe);
  };

  return entries.find(matcher) || entries[0];
}

async function stageUpdate(options: {
  manifest: UpdateManifest;
  asset: UpdateAsset;
  stagingDir: string;
}) {
  const { manifest, asset, stagingDir } = options;
  const versionTag = `v${manifest.version}`;
  const versionDir = path.join(stagingDir, versionTag);
  const archivePath = path.join(versionDir, asset.file);
  const extractDir = path.join(versionDir, 'extracted');

  ensureDir(versionDir);

  console.info(`[updater] Downloading ${asset.file} for version ${manifest.version}`);
  await downloadAsset(asset.downloadUrl, archivePath);
  verifyChecksum(archivePath, asset.checksum);

  console.info('[updater] Extracting archive');
  const zip = new AdmZip(archivePath);
  zip.extractAllTo(extractDir, true);
  const platform = getPlatformDescriptor();
  const entry = findBinaryInArchive(zip, platform?.os === 'windows');
  if (!entry) {
    throw new Error('Could not locate agent binary inside the archive');
  }

  const extractedBinaryPath = path.join(extractDir, entry.entryName);
  const binaryName = path.basename(process.execPath);
  const stagedBinaryPath = path.join(versionDir, binaryName);
  fs.copyFileSync(extractedBinaryPath, stagedBinaryPath);
  fs.chmodSync(stagedBinaryPath, 0o755);

  const info = {
    version: manifest.version,
    downloadedAt: new Date().toISOString(),
    archive: asset.file,
    archiveChecksum: asset.checksum,
    stagedBinary: stagedBinaryPath,
    originalBinary: process.execPath,
    notes: manifest.notes ?? null,
  };
  fs.writeFileSync(
    path.join(versionDir, 'update-info.json'),
    JSON.stringify(info, null, 2),
    'utf-8',
  );

  writeHelperScripts({
    versionDir,
    binaryName,
    stagedBinaryPath,
    originalBinary: process.execPath,
  });

  console.info(
    `[updater] Update ${manifest.version} staged at ${versionDir}. Restart with '--install-staged-update' to apply.`,
  );
}

function writeHelperScripts(options: {
  versionDir: string;
  binaryName: string;
  stagedBinaryPath: string;
  originalBinary: string;
}) {
  const { versionDir, binaryName, stagedBinaryPath, originalBinary } = options;
  const linuxScript = `#!/usr/bin/env bash
set -euo pipefail
echo "Ensure the Resonance Agent service is stopped before applying the update."
SOURCE="$(dirname "$0")/${binaryName}"
TARGET="${originalBinary}"
cp "$SOURCE" "$TARGET"
chmod +x "$TARGET"
echo "Resonance Agent updated. Restart the service to use the new version."
`;
  fs.writeFileSync(path.join(versionDir, 'apply-update.sh'), linuxScript, 'utf-8');
  fs.chmodSync(path.join(versionDir, 'apply-update.sh'), 0o755);

  const winScript = `# Auto-generated by Resonance Agent
# Run as Administrator after stopping the Resonance Agent service.
$SourcePath = "$PSScriptRoot\\${binaryName}"
$TargetPath = "${originalBinary.replace(/\\/g, '\\\\')}"
Copy-Item -Path $SourcePath -Destination $TargetPath -Force
Write-Output "Resonance Agent updated. Restart the service to use the new version."
`;
  fs.writeFileSync(path.join(versionDir, 'apply-update.ps1'), winScript, 'utf-8');
}

async function checkForUpdates(manifestUrl: string, stagingDir: string) {
  try {
    const manifest = await fetchManifest(manifestUrl);
    if (!manifest || !manifest.version) {
      console.warn('[updater] Manifest missing version');
      return;
    }

    if (compareVersions(manifest.version, CURRENT_VERSION) <= 0) {
      return;
    }

    const platform = getPlatformDescriptor();
    if (!platform) {
      console.warn('[updater] Unsupported platform for auto-update');
      return;
    }

    const asset = manifest.assets.find(
      (item) => item.os === platform.os && item.arch === platform.arch,
    );

    if (!asset) {
      console.warn('[updater] No matching asset in update manifest');
      return;
    }

    await stageUpdate({ manifest, asset, stagingDir });
  } catch (error) {
    console.error(`[updater] Update check failed: ${(error as Error).message}`);
  }
}

export function scheduleAutoUpdate(options: AutoUpdateOptions = {}) {
  const manifestUrl = options.manifestUrl;
  if (!manifestUrl) {
    return;
  }

  const interval = Math.max(options.intervalMs ?? DEFAULT_INTERVAL_MS, MIN_INTERVAL_MS);
  const stagingDir = determineStagingDir(options.stagingDir);
  ensureDir(stagingDir);

  const run = async () => {
    await checkForUpdates(manifestUrl, stagingDir);
    updateTimer = setTimeout(run, interval);
  };

  void run();
}

function readUpdateInfo(versionDir: string) {
  const infoPath = path.join(versionDir, 'update-info.json');
  if (!fs.existsSync(infoPath)) {
    return null;
  }
  try {
    const raw = fs.readFileSync(infoPath, 'utf-8');
    return JSON.parse(raw) as {
      version: string;
      stagedBinary: string;
      originalBinary: string;
    };
  } catch (error) {
    console.warn(`[updater] Failed to read update info: ${(error as Error).message}`);
    return null;
  }
}

function listStagedVersions(stagingDir: string): string[] {
  if (!fs.existsSync(stagingDir)) {
    return [];
  }
  return fs
    .readdirSync(stagingDir)
    .filter((entry) => entry.startsWith('v'))
    .sort(compareVersions);
}

export function installStagedUpdate(options: { stagingDir?: string; version?: string } = {}): InstallResult {
  const stagingDir = determineStagingDir(options.stagingDir);
  const stagedVersions = listStagedVersions(stagingDir);
  if (stagedVersions.length === 0) {
    return { installed: false, message: 'No staged updates found.' };
  }

  const versionTag = options.version
    ? `v${options.version.replace(/^v/i, '')}`
    : stagedVersions[stagedVersions.length - 1];

  const versionDir = path.join(stagingDir, versionTag);
  const info = readUpdateInfo(versionDir);
  if (!info) {
    return { installed: false, message: `Missing update metadata for ${versionTag}` };
  }

  const stagedBinary = info.stagedBinary;
  if (!fs.existsSync(stagedBinary)) {
    return { installed: false, message: `Staged binary not found: ${stagedBinary}` };
  }

  const targetPath = info.originalBinary || process.execPath;
  const backupPath = `${targetPath}.bak`;

  try {
    if (process.platform !== 'win32') {
      if (fs.existsSync(backupPath)) {
        fs.rmSync(backupPath, { force: true });
      }
      fs.copyFileSync(targetPath, backupPath);
      fs.copyFileSync(stagedBinary, targetPath);
      fs.chmodSync(targetPath, 0o755);
      return { installed: true, message: `Update ${info.version} installed. Restart the agent.` };
    }

    // Windows: advise manual script (cannot replace locked executable reliably)
    return {
      installed: false,
      message:
        'Automatic replacement on Windows requires the service to be stopped. Run apply-update.ps1 from the staged update directory as Administrator.',
    };
  } catch (error) {
    return {
      installed: false,
      message: `Failed to install update: ${(error as Error).message}`,
    };
  }
}

export function handleCliUpdateCommand(options: { stagingDir?: string } = {}): boolean {
  if (!process.argv.includes('--install-staged-update')) {
    return false;
  }

  const result = installStagedUpdate(options);
  if (result.installed) {
    console.log(result.message ?? 'Update installed.');
    process.exit(0);
  } else {
    console.error(result.message ?? 'Failed to install staged update.');
    process.exit(1);
  }
  return true;
}

export function stopAutoUpdateWatcher() {
  if (updateTimer) {
    clearTimeout(updateTimer);
    updateTimer = null;
  }
}

