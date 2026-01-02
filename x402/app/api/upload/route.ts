import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { saveFile } from '@/lib/storage'
import { getCurrentUser } from '@/lib/auth'
import { logger } from '@/lib/logger'
import { nanoid } from 'nanoid'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  let user: any = null
  let sessionId: string | undefined = undefined
  
  try {
    // Try to get authenticated user (optional - allows anonymous uploads)
    const authHeader = request.headers.get('authorization')
    user = await getCurrentUser(authHeader)

    // Parse form data
    const formData = await request.formData()
    const file = formData.get('file') as File

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 })
    }

    // Validate file type
    if (file.type !== 'application/pdf') {
      return NextResponse.json({ error: 'Only PDF files are supported' }, { status: 400 })
    }

    // Convert File to Buffer
    const arrayBuffer = await file.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)

    // Save file to storage
    const { filePath, fileName } = await saveFile(buffer, file.name, 'uploads')

    // Generate session ID for anonymous jobs
    if (!user) {
      sessionId = nanoid(21) // Generate unique session ID
    }

    // Create job record (userId can be null for anonymous jobs)
    const job = await prisma.job.create({
      data: {
        userId: user?.id || null,
        sessionId: sessionId || null,
        fileName: file.name,
        filePath,
        status: 'pending',
        paymentStatus: 'pending',
      },
    })

    logger.info('File uploaded', {
      jobId: job.id,
      userId: user?.id || 'anonymous',
      sessionId: sessionId || null,
      fileName: file.name,
      fileSize: file.size,
    })

    return NextResponse.json({
      jobId: job.id,
      status: job.status,
      message: 'File uploaded successfully',
      sessionId: sessionId || undefined, // Return sessionId for anonymous jobs
    })
  } catch (error) {
    logger.error('Upload error', {
      error: String(error),
      userId: user?.id,
      sessionId,
    })
    return NextResponse.json(
      { error: 'Failed to upload file' },
      { status: 500 }
    )
  }
}

