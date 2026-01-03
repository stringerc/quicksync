import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { readFile } from '@/lib/storage'
import { logger } from '@/lib/logger'

export const dynamic = 'force-dynamic'

/**
 * Preview endpoint - returns watermarked preview files
 * No authentication required (uses sessionId or public access)
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string; format: string } }
) {
  const { id, format } = params
  
  try {
    if (!['csv', 'qbo'].includes(format)) {
      return NextResponse.json({ error: 'Invalid format' }, { status: 400 })
    }

    // Get job
    const job = await prisma.job.findUnique({
      where: { id },
    })

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    // Check if job is ready for preview
    const isReady = job.status === 'completed' || job.status === 'needs_review'
    if (!isReady) {
      return NextResponse.json(
        { error: 'Preview not ready yet' },
        { status: 400 }
      )
    }

    // Get preview file path
    const previewFilePath = format === 'csv' 
      ? job.previewCsvFilePath 
      : job.previewQboFilePath

    if (!previewFilePath) {
      // Fallback: if no preview file, return error
      return NextResponse.json(
        { error: 'Preview not available' },
        { status: 404 }
      )
    }

    // Read preview file
    const previewBuffer = await readFile(previewFilePath)

    // Set appropriate content type
    const contentType = format === 'csv'
      ? 'text/html' // CSV preview is HTML
      : 'application/pdf' // QBO preview is PDF

    logger.info('Preview accessed', {
      jobId: id,
      format,
      hasPreview: !!previewFilePath,
    })

    return new NextResponse(previewBuffer as any, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `inline; filename="preview.${format === 'csv' ? 'html' : 'pdf'}"`,
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
      },
    })
  } catch (error) {
    logger.error('Preview error', {
      jobId: id,
      format,
      error: String(error),
    })
    return NextResponse.json(
      { error: 'Failed to load preview' },
      { status: 500 }
    )
  }
}

