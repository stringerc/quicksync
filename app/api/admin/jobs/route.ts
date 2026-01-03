import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
import { prisma } from '@/lib/db'
import { getCurrentUser } from '@/lib/auth'
import { logger } from '@/lib/logger'

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    const user = await getCurrentUser(authHeader)

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Check if user is admin
    const adminEmails = process.env.ADMIN_EMAILS?.split(',').map((e) => e.trim()) || []
    if (!adminEmails.includes(user.email)) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }

    // Get last 50 jobs
    const jobs = await prisma.job.findMany({
      take: 50,
      orderBy: { createdAt: 'desc' },
      include: {
        user: {
          select: {
            email: true,
          },
        },
      },
    })

    logger.info('Admin jobs view accessed', { adminEmail: user.email, jobCount: jobs.length })

    return NextResponse.json({
      jobs: jobs.map((job) => ({
        id: job.id,
        fileName: job.fileName,
        status: job.status,
        paymentStatus: job.paymentStatus,
        createdAt: job.createdAt.toISOString(),
        processedAt: job.processedAt?.toISOString(),
        paidAt: job.paidAt?.toISOString(),
        userId: job.userId,
        userEmail: job.user?.email || null,
        rowCount: job.rowCount,
        confidenceScore: job.confidenceScore,
        stripePaymentId: job.stripePaymentId,
        stripeCheckoutSessionId: job.stripeCheckoutSessionId,
      })),
    })
  } catch (error) {
    logger.error('Admin jobs view error', {
      error: String(error),
    })
    return NextResponse.json(
      { error: 'Failed to fetch jobs' },
      { status: 500 }
    )
  }
}

