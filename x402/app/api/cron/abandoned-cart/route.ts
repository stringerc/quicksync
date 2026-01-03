import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { sendAbandonedCartEmail } from '@/lib/email'
import { logger } from '@/lib/logger'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/**
 * Vercel Cron Job: Abandoned Cart Emails
 * 
 * Runs daily to send reminder emails to users who:
 * - Uploaded a file (job status: completed)
 * - Haven't paid (paymentStatus: pending)
 * - Created > 24 hours ago
 * - Haven't received abandoned cart email yet
 * 
 * Configure in vercel.json:
 * {
 *   "crons": [{
 *     "path": "/api/cron/abandoned-cart",
 *     "schedule": "0 10 * * *"  // Daily at 10 AM UTC
 *   }]
 * }
 */
export async function GET(request: NextRequest) {
  // Verify cron secret (optional but recommended)
  const authHeader = request.headers.get('authorization')
  const cronSecret = process.env.CRON_SECRET
  
  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    // Find jobs that qualify for abandoned cart email
    const twentyFourHoursAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
    
    const abandonedJobs = await prisma.job.findMany({
      where: {
        status: 'completed',
        paymentStatus: 'pending',
        createdAt: {
          lt: twentyFourHoursAgo, // Created more than 24 hours ago
        },
        abandonedCartEmailSentAt: null, // Haven't sent email yet
        userId: {
          not: null, // Must have a user (need email)
        },
      },
      include: {
        user: {
          select: {
            id: true,
            email: true,
          },
        },
      },
      take: 100, // Process up to 100 jobs at a time to avoid timeout
    })

    logger.info('Abandoned cart cron job started', {
      jobsFound: abandonedJobs.length,
    })

    let emailsSent = 0
    let errors = 0

    for (const job of abandonedJobs) {
      if (!job.user?.email) {
        logger.warn('Job has no user email', { jobId: job.id })
        continue
      }

      try {
        // Send abandoned cart email
        const sent = await sendAbandonedCartEmail(
          job.user.email,
          job.id,
          job.fileName
        )

        if (sent) {
          // Mark email as sent
          await prisma.job.update({
            where: { id: job.id },
            data: {
              abandonedCartEmailSentAt: new Date(),
            },
          })

          emailsSent++
          logger.info('Abandoned cart email sent', {
            jobId: job.id,
            email: job.user.email,
            fileName: job.fileName,
          })
        } else {
          logger.warn('Failed to send abandoned cart email (SMTP not configured?)', {
            jobId: job.id,
            email: job.user.email,
          })
        }
      } catch (error) {
        errors++
        logger.error('Error sending abandoned cart email', {
          jobId: job.id,
          email: job.user.email,
          error: String(error),
        })
      }
    }

    return NextResponse.json({
      success: true,
      jobsFound: abandonedJobs.length,
      emailsSent,
      errors,
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    logger.error('Abandoned cart cron job error', {
      error: String(error),
      stack: error instanceof Error ? error.stack : undefined,
    })

    return NextResponse.json(
      {
        success: false,
        error: String(error),
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    )
  }
}

