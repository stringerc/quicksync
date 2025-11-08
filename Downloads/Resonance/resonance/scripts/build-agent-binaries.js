#!/usr/bin/env node
/**
 * Build packaged Resonance Agent binaries, archives, and update manifests.
 *
 * Steps:
 * 1. Compile TypeScript -> dist/
 * 2. Run pkg to produce self-contained executables in dist-binaries/
 * 3. Zip each binary, compute hashes, and emit manifest + update manifest
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const archiver = require('archiver');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const DIST_DIR = path.join(PROJECT_ROOT, 'dist');
const OUTPUT_DIR = path.join(PROJECT_ROOT, 'dist-binaries');
const ENTRYPOINT = path.join(DIST_DIR, 'agent', 'index_secure.js');
const PACKAGE_META = require('../package.json');

function run(command, options = {}) {
  console.log(`\n▶ ${command}`);
  execSync(command, {
    stdio: 'inherit',
    cwd: PROJECT_ROOT,
    env: process.env,
    ...options,
  });
}

function ensureCleanOutputDir() {
  if (fs.existsSync(OUTPUT_DIR)) {
    fs.rmSync(OUTPUT_DIR, { recursive: true, force: true });
  }
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

function assertBuiltEntrypoint() {
  if (!fs.existsSync(ENTRYPOINT)) {
    throw new Error(
      `Expected compiled entrypoint at ${ENTRYPOINT}. Did the TypeScript build fail?`
    );
  }
}

function computeSha256(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function writeManifest(targets) {
  const manifest = {
    generatedAt: new Date().toISOString(),
    entry: 'resonance/dist/agent/index_secure.ts',
    pkgVersion: PACKAGE_META.version || '0.0.0',
    targets,
  };
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'manifest.json'),
    JSON.stringify(manifest, null, 2),
    'utf-8'
  );
}

function writeUpdateManifest(artifacts) {
  const updateManifest = {
    version: PACKAGE_META.version || '0.0.0',
    publishedAt: new Date().toISOString(),
    assets: artifacts.map((artifact) => ({
      os: artifact.os,
      arch: artifact.arch,
      file: artifact.archive,
      checksum: `sha256:${artifact.archiveSha}`,
      downloadUrl: `https://downloads.resonance.example/${artifact.archive}`, // replace before publishing
    })),
    notes:
      'Automated build. Update the downloadUrl fields to your CDN or release storage before publishing.',
  };

  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'update-manifest.json'),
    JSON.stringify(updateManifest, null, 2),
    'utf-8'
  );
}

function zipBinary({ sourcePath, archivePath, entryName, extraFiles = [] }) {
  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(archivePath);
    const archive = archiver('zip', { zlib: { level: 9 } });

    output.on('close', resolve);
    archive.on('warning', (err) => {
      if (err.code === 'ENOENT') {
        console.warn(err);
      } else {
        reject(err);
      }
    });
    archive.on('error', reject);

    archive.pipe(output);
    archive.file(sourcePath, { name: entryName });
    extraFiles.forEach((file) => {
      if (fs.existsSync(file.path)) {
        archive.file(file.path, { name: file.name });
      }
    });
    archive.finalize();
  });
}

async function main() {
  console.log('Resonance Agent binary builder');

  // Step 1: compile TypeScript
  run('npm run build --silent');
  assertBuiltEntrypoint();

  // Step 2: clean and create output directory
  ensureCleanOutputDir();

  // Step 3: package with pkg
  const targets = [
    'node18-macos-x64',
    'node18-linux-x64',
    'node18-win-x64',
  ];

  const pkgCommand = [
    'npx',
    'pkg',
    `"${ENTRYPOINT}"`,
    '--compress',
    'GZip',
    '--out-path',
    `"${OUTPUT_DIR}"`,
    '--targets',
    targets.join(','),
  ].join(' ');
  run(pkgCommand);

  const renameMap = {
    'node18-macos-x64': {
      src: 'index_secure-macos',
      dest: 'resonance-agent-macos-x64',
      os: 'macos',
      arch: 'x64',
      archive: 'resonance-agent-macos-x64.zip',
      entryName: 'resonance-agent',
    },
    'node18-linux-x64': {
      src: 'index_secure-linux',
      dest: 'resonance-agent-linux-x64',
      os: 'linux',
      arch: 'x64',
      archive: 'resonance-agent-linux-x64.zip',
      entryName: 'resonance-agent',
    },
    'node18-win-x64': {
      src: 'index_secure-win.exe',
      dest: 'resonance-agent-windows-x64.exe',
      os: 'windows',
      arch: 'x64',
      archive: 'resonance-agent-windows-x64.zip',
      entryName: 'resonance-agent.exe',
    },
  };

  const artifacts = [];

  targets.forEach((target) => {
    const rule = renameMap[target];
    if (!rule) return;
    const src = path.join(OUTPUT_DIR, rule.src);
    const dest = path.join(OUTPUT_DIR, rule.dest);
    if (fs.existsSync(src)) {
      fs.renameSync(src, dest);
      artifacts.push({
        target,
        os: rule.os,
        arch: rule.arch,
        binary: rule.dest,
        binaryPath: dest,
        archive: rule.archive,
        archivePath: path.join(OUTPUT_DIR, rule.archive),
        entryName: rule.entryName,
      });
    }
  });

  // Step 4: zip binaries & compute checksums
  for (const artifact of artifacts) {
    await zipBinary({
      sourcePath: artifact.binaryPath,
      archivePath: artifact.archivePath,
      entryName: artifact.entryName,
      extraFiles: [
        {
          path: path.join(PROJECT_ROOT, 'docs', 'desktop-agent', 'README.md'),
          name: 'README-desktop-agent.md',
        },
        {
          path: path.join(PROJECT_ROOT, 'policy', 'defaults.json'),
          name: 'policy-defaults.json',
        },
      ],
    });

    artifact.binarySha = computeSha256(artifact.binaryPath);
    artifact.archiveSha = computeSha256(artifact.archivePath);
  }

  writeManifest(
    artifacts.map((artifact) => ({
      target: artifact.target,
      binary: artifact.binary,
      binaryChecksum: artifact.binarySha,
      archive: artifact.archive,
      archiveChecksum: artifact.archiveSha,
    }))
  );

  writeUpdateManifest(artifacts);

  console.log('\n✅ Resonance Agent binaries ready in dist-binaries/');
  console.log('   Zip archives and update manifests generated.');
  console.log('   Next steps: sign installers per platform and publish artifacts.');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

