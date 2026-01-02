import { NextRequest, NextResponse } from 'next/server'
import { stripe, PRICE_PER_FILE } from '@/lib/stripe'
import { prisma } from '@/lib/db'
import { getCurrentUser } from '@/lib/auth'
import { logger } from '@/lib/logger'
import { getCreditBalance } from '@/lib/credits'
import { isEligibleForFreeFirstFile, isEmailEligibleForFreeFirstFile } from '@/lib/free-first-file'
import * as Sentry from '@sentry/nextjs'

export const dynamic = 'force-dynamic'

export async function POST(request: NextRequest) {
  let user: any = null
  let jobId: string | undefined = undefined
  
  try {
    // Try to get authenticated user (optional for anonymous jobs)
    const authHeader = request.headers.get('authorization')
    user = await getCurrentUser(authHeader)

    const body = await request.json()
    jobId = body.jobId
    const email = body.email // Email for anonymous jobs
    const sessionId = body.sessionId // Session ID for anonymous jobs

    if (!jobId) {
      return NextResponse.json({ error: 'Job ID required' }, { status: 400 })
    }

    // Get job
    const job = await prisma.job.findUnique({
      where: { id: jobId },
    })

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    // Verify access: user must match OR sessionId must match (for anonymous jobs)
    if (job.userId && job.userId !== user?.id) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    if (!job.userId && job.sessionId !== sessionId) {
      return NextResponse.json({ error: 'Invalid session' }, { status: 403 })
    }

    // If anonymous job, create/find user by email
    if (!job.userId && email) {
      // Validate email
      if (!email.includes('@')) {
        return NextResponse.json({ error: 'Valid email required' }, { status: 400 })
      }

      // Find or create user
      let existingUser = await prisma.user.findUnique({
        where: { email },
      })

      if (!existingUser) {
        existingUser = await prisma.user.create({
          data: { email },
        })
      }

      // Link job to user
      await prisma.job.update({
        where: { id: jobId },
        data: { userId: existingUser.id },
      })

      user = existingUser
      logger.info('Job linked to user', {
        jobId,
        userId: user.id,
        email,
      })
    }

    if (!user) {
      return NextResponse.json({ error: 'Email required for anonymous jobs' }, { status: 400 })
    }

    if (job.paymentStatus === 'paid') {
      return NextResponse.json({ error: 'Already paid' }, { status: 400 })
    }

    // Check if user is eligible for free first file
    const isFreeFirstFile = await isEligibleForFreeFirstFile(user.id)

    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

    if (isFreeFirstFile) {
      // Free first file - mark as paid directly without Stripe
      await prisma.job.update({
        where: { id: jobId },
        data: {
          paymentStatus: 'paid',
          paidAt: new Date(),
        },
      })

      logger.info('Free first file granted', {
        jobId,
        userId: user.id,
        email: user.email,
      })

      return NextResponse.json({
        free: true,
        message: 'Free first file! Your job is now ready for download.',
      })
    }

    // Create Stripe Checkout session for paid file
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: `PDF to CSV Conversion - ${job.fileName}`,
              description: 'Convert PDF financial statement to CSV/QBO format',
            },
            unit_amount: PRICE_PER_FILE,
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${appUrl}/jobs/${jobId}?payment=success`,
      cancel_url: `${appUrl}/jobs/${jobId}?payment=canceled`,
      client_reference_id: jobId,
      customer_email: email || user.email, // Pre-fill email in Stripe Checkout
      metadata: {
        jobId,
        userId: user.id,
        purchaseType: 'job', // Single file purchase
        email: email || user.email,
      },
    })

    // Store checkout session ID for tracking
    await prisma.job.update({
      where: { id: jobId },
      data: {
        stripeCheckoutSessionId: session.id,
      },
    })

    logger.info('Checkout session created', {
      jobId,
      sessionId: session.id,
      userId: user.id,
    })

    return NextResponse.json({
      sessionId: session.id,
      url: session.url,
      free: false,
    })
  } catch (error) {
    // Capture exception in Sentry
    Sentry.captureException(error, {
      tags: {
        route: 'create-checkout',
        userId: user?.id,
        jobId,
      },
    })
    
    logger.error('Checkout creation error', {
      error: String(error),
      userId: user?.id,
      jobId,
    })
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    )
  }
}

