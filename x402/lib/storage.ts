import { promises as fs } from 'fs'
import path from 'path'
import { randomBytes } from 'crypto'
import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand } from '@aws-sdk/client-s3'
import { getSignedUrl } from '@aws-sdk/s3-request-presigner'

const STORAGE_TYPE = process.env.STORAGE_TYPE || 'local'
const STORAGE_PATH = process.env.STORAGE_PATH || './storage'

// S3 configuration
let s3Client: S3Client | null = null
if (STORAGE_TYPE === 's3') {
  const endpoint = process.env.AWS_S3_ENDPOINT // For Cloudflare R2, set this
  const region = process.env.AWS_REGION || 'us-east-1'
  
  s3Client = new S3Client({
    region,
    endpoint: endpoint || undefined,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
    },
    forcePathStyle: endpoint ? true : false, // Required for R2 and some S3-compatible services
  })
}

const S3_BUCKET = process.env.AWS_S3_BUCKET

export interface StorageResult {
  filePath: string // For S3, this is the object key
  fileName: string
}

/**
 * Save uploaded file to storage
 */
export async function saveFile(
  file: Buffer,
  originalName: string,
  subfolder: string = 'uploads'
): Promise<StorageResult> {
  // Generate unique filename
  const ext = path.extname(originalName)
  const baseName = path.basename(originalName, ext)
  const uniqueName = `${baseName}-${randomBytes(8).toString('hex')}${ext}`
  
  if (STORAGE_TYPE === 'local') {
    // Ensure storage directory exists
    const storageDir = path.join(STORAGE_PATH, subfolder)
    await fs.mkdir(storageDir, { recursive: true })

    const filePath = path.join(storageDir, uniqueName)
    await fs.writeFile(filePath, file)

    return {
      filePath,
      fileName: uniqueName,
    }
  }

  if (STORAGE_TYPE === 's3' && s3Client && S3_BUCKET) {
    const objectKey = `${subfolder}/${uniqueName}`
    
    await s3Client.send(
      new PutObjectCommand({
        Bucket: S3_BUCKET,
        Key: objectKey,
        Body: file,
        ContentType: 'application/pdf',
      })
    )

    return {
      filePath: objectKey, // Store the S3 key, not a filesystem path
      fileName: uniqueName,
    }
  }

  throw new Error(`Storage type "${STORAGE_TYPE}" not properly configured`)
}

/**
 * Read file from storage
 */
export async function readFile(filePath: string): Promise<Buffer> {
  if (STORAGE_TYPE === 'local') {
    return await fs.readFile(filePath)
  }

  if (STORAGE_TYPE === 's3' && s3Client && S3_BUCKET) {
    const command = new GetObjectCommand({
      Bucket: S3_BUCKET,
      Key: filePath, // filePath is the S3 key
    })

    const response = await s3Client.send(command)
    
    if (!response.Body) {
      throw new Error('File not found in S3')
    }

    // Convert stream to buffer
    const chunks: Uint8Array[] = []
    for await (const chunk of response.Body as any) {
      chunks.push(chunk)
    }
    return Buffer.concat(chunks)
  }

  throw new Error(`Storage type "${STORAGE_TYPE}" not properly configured`)
}

/**
 * Delete file from storage
 */
export async function deleteFile(filePath: string): Promise<void> {
  if (STORAGE_TYPE === 'local') {
    await fs.unlink(filePath)
    return
  }

  if (STORAGE_TYPE === 's3' && s3Client && S3_BUCKET) {
    await s3Client.send(
      new DeleteObjectCommand({
        Bucket: S3_BUCKET,
        Key: filePath, // filePath is the S3 key
      })
    )
    return
  }

  throw new Error(`Storage type "${STORAGE_TYPE}" not properly configured`)
}

/**
 * Generate a signed URL for downloading (S3 only)
 * Returns the filePath for local storage (use readFile instead)
 */
export async function getSignedDownloadUrl(
  filePath: string,
  expiresIn: number = 3600
): Promise<string> {
  if (STORAGE_TYPE === 'local') {
    // For local storage, return the path (not a URL)
    // Caller should use readFile instead
    return filePath
  }

  if (STORAGE_TYPE === 's3' && s3Client && S3_BUCKET) {
    const command = new GetObjectCommand({
      Bucket: S3_BUCKET,
      Key: filePath,
    })

    return await getSignedUrl(s3Client, command, { expiresIn })
  }

  throw new Error(`Storage type "${STORAGE_TYPE}" not properly configured`)
}

/**
 * Get full path for storage operations (local only)
 */
export function getStoragePath(relativePath: string): string {
  if (STORAGE_TYPE === 'local') {
    return path.join(STORAGE_PATH, relativePath)
  }
  // For S3, return the key as-is
  return relativePath
}

