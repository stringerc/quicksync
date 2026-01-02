import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { getCurrentUser } from '@/lib/auth'
import { logger } from '@/lib/logger'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const authHeader = request.headers.get('authorization')
    const user = await getCurrentUser(authHeader)

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const job = await prisma.job.findUnique({
      where: { id: params.id },
    })

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    if (job.userId !== user.id) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }

    await prisma.job.update({
      where: { id: params.id },
      data: {
        reviewRequestedAt: new Date(),
      },
    })

    logger.info('Review requested', {
      jobId: params.id,
      userId: user.id,
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    logger.error('Request review error', {
      error: String(error),
      jobId: params.id,
    })
    return NextResponse.json(
      { error: 'Failed to request review' },
      { status: 500 }
    )
  }
}

