import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { readFile } from '@/lib/storage'
import { getCurrentUser } from '@/lib/auth'
import { logger } from '@/lib/logger'
import { getCreditBalance, redeemCredit } from '@/lib/credits'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string; format: string } }
) {
  const { id, format } = params
  let user: any = null
  
  try {
    const authHeader = request.headers.get('authorization')
    user = await getCurrentUser(authHeader)

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

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

    if (job.userId !== user.id) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }

    // Check status first
    const isReady = job.status === 'completed' || job.status === 'needs_review'
    if (!isReady) {
      return NextResponse.json(
        { error: 'File not ready for download' },
        { status: 400 }
      )
    }

    // Payment gate: Allow downloads if paid OR if user has credits
    const isPaid = job.paymentStatus === 'paid' && job.paidAt !== null
    const hasCredits = await getCreditBalance(user.id) >= 1

    if (!isPaid && !hasCredits) {
      return NextResponse.json(
        { error: 'Payment or credits required' },
        { status: 402 }
      )
    }

    // If using credits, redeem one (atomic operation)
    if (!isPaid && hasCredits) {
      const redeemed = await redeemCredit(user.id)
      if (!redeemed) {
        return NextResponse.json(
          { error: 'Insufficient credits' },
          { status: 402 }
        )
      }

      // Mark job as credit-redeemed
      await prisma.job.update({
        where: { id },
        data: {
          creditRedeemedAt: new Date(),
        },
      })

      logger.info('Credit redeemed for download', {
        jobId: id,
        userId: user.id,
        format,
      })
    }

    // Get file path
    const filePath = format === 'csv' ? job.csvFilePath : job.qboFilePath

    if (!filePath) {
      return NextResponse.json(
        { error: 'File not found' },
        { status: 404 }
      )
    }

    // Read and return file
    const fileBuffer = await readFile(filePath)
    const contentType = format === 'csv' ? 'text/csv' : 'application/octet-stream'
    const fileName = `${job.fileName.replace('.pdf', '')}.${format}`

    logger.info('File downloaded', {
      jobId: id,
      format,
      userId: user.id,
      fileName: job.fileName,
    })

    return new NextResponse(fileBuffer as any, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `attachment; filename="${fileName}"`,
      },
    })
  } catch (error) {
    logger.error('Download error', {
      jobId: id,
      format,
      error: String(error),
      userId: user?.id,
    })
    return NextResponse.json(
      { error: 'Failed to download file' },
      { status: 500 }
    )
  }
}

