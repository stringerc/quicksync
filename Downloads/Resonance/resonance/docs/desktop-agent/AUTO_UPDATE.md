## Auto-Update Strategy

The Resonance Agent can self-update by polling a hosted `update-manifest.json` and downloading the appropriate archive. This document outlines the recommended protocol.

### Manifest Format

Generated automatically at `dist-binaries/update-manifest.json`:

```json
{
  "version": "0.1.0",
  "publishedAt": "2025-11-08T00:25:52.003Z",
  "assets": [
    {
      "os": "macos",
      "arch": "x64",
      "file": "resonance-agent-macos-x64.zip",
      "checksum": "sha256:…",
      "downloadUrl": "https://downloads.resonance.example/resonance-agent-macos-x64.zip"
    }
  ],
  "notes": "Release highlights…"
}
```

- Update `downloadUrl` to point at your CDN or object storage.
- Optionally add `signature` for detached signatures.

### Agent Workflow

1. **Check manifest** on startup and every `N` hours (configurable).
2. **Compare versions** (`semver.compare`).
3. **Download archive** if newer version exists.
4. **Verify checksum** (SHA-256) before extraction.
5. **Unpack** to staging directory (e.g., `%PROGRAMDATA%\Resonance\updates\`, `/var/lib/resonance-agent/updates/`).
6. **Swap binary**:
   - On Unix: replace symlink or copy binary, restart service.
   - On Windows: use `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING` + scheduled restart.
7. **Cleanup** old versions, keeping last two releases for rollback.

### Security Considerations

- Serve manifest & archives over HTTPS.
- Optionally sign archives with detached signature and include `signature` field.
- Pin TLS certificates or use short-lived signed URLs for downloads.
- Validate manifest payload before acting (JSON schema + version sanity checks).

### Client API Sketch (TypeScript)

```ts
import crypto from 'crypto';
import fetch from 'node-fetch';
import { createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';

interface UpdateManifest {
  version: string;
  assets: Array<{
    os: string;
    arch: string;
    file: string;
    checksum: string; // sha256:<hex>
    downloadUrl: string;
  }>;
}

async function fetchManifest(url: string): Promise<UpdateManifest> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch manifest: ${res.status}`);
  return res.json();
}

async function downloadWithSha256(url: string, dest: string, expected: string) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);

  const hash = crypto.createHash('sha256');
  const file = createWriteStream(dest);

  res.body.on('data', (chunk) => hash.update(chunk));
  await pipeline(res.body, file);

  const digest = hash.digest('hex');
  if (expected !== `sha256:${digest}`) {
    throw new Error(`Checksum mismatch: expected ${expected}, got sha256:${digest}`);
  }
}
```

### Hosting

- Host `update-manifest.json` and archives on a CDN (S3 + CloudFront, Azure Blob + CDN).
- Version them by release (`/releases/agent-v1.2.3/update-manifest.json`) so older clients can still reach matching payloads.
- Add a stable pointer (e.g., `/resonance-agent/latest/update-manifest.json`) that always references the newest release.

### Rollback

1. Publish a manifest pointing back to the previous version.
2. Clients download the older archive and reinstall.
3. Maintain telemetry for upgrade success/failure rates.

### Integration Checklist

- [ ] Implement client-side updater invoking the above workflow.
- [ ] Wire the manifest URL to environment/config.
- [ ] Instrument success/failure metrics.
- [ ] Expose `resonance-agent update` CLI command for immediate upgrade.
- [ ] Document offline/manual update procedure.

