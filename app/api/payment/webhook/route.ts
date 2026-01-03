import { NextRequest, NextResponse } from 'next/server'
import { stripe } from '@/lib/stripe'
import { prisma } from '@/lib/db'
import Stripe from 'stripe'
import { logger } from '@/lib/logger'
import { addCredits } from '@/lib/credits'

export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  const body = await request.text()
  const signature = request.headers.get('stripe-signature')

  if (!signature || !process.env.STRIPE_WEBHOOK_SECRET) {
    return NextResponse.json(
      { error: 'Missing signature or webhook secret' },
      { status: 400 }
    )
  }

  let event: Stripe.Event

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET
    )
  } catch (err) {
    logger.error('Webhook signature verification failed', {
      error: String(err),
    })
    return NextResponse.json(
      { error: 'Invalid signature' },
      { status: 400 }
    )
  }

  try {
    if (event.type === 'checkout.session.completed') {
      const session = event.data.object as Stripe.Checkout.Session
      const purchaseType = session.metadata?.purchaseType || 'job'
      const userId = session.metadata?.userId

      if (purchaseType === 'credit_pack') {
        // Credit pack purchase
        if (!userId) {
          logger.error('No userId for credit pack purchase', { sessionId: session.id })
          return NextResponse.json({ error: 'No userId' }, { status: 400 })
        }

        const creditsToAdd = parseInt(session.metadata?.credits || '10')
        await addCredits(userId, creditsToAdd, 'purchase')

        logger.info('Credit pack purchased', {
          userId,
          credits: creditsToAdd,
          sessionId: session.id,
        })
      } else {
        // Single job payment
        const jobId = session.client_reference_id || session.metadata?.jobId

        if (!jobId) {
          logger.error('No jobId in checkout session', { sessionId: session.id })
          return NextResponse.json({ error: 'No jobId' }, { status: 400 })
        }

        // Update job payment status
        await prisma.job.update({
          where: { id: jobId },
          data: {
            paymentStatus: 'paid',
            stripePaymentId: session.payment_intent as string,
            stripeCheckoutSessionId: session.id,
            paidAt: new Date(),
          },
        })

        logger.info('Payment confirmed', {
          jobId,
          sessionId: session.id,
          paymentIntentId: typeof session.payment_intent === 'string' ? session.payment_intent : session.payment_intent?.id || null,
        })
      }
    } else if (event.type === 'payment_intent.succeeded') {
      const paymentIntent = event.data.object as Stripe.PaymentIntent

      // Find job by payment_intent ID
      const job = await prisma.job.findFirst({
        where: { stripePaymentId: paymentIntent.id },
      })

      if (job && job.paymentStatus !== 'paid') {
        // Update if not already marked as paid (defensive check)
        await prisma.job.update({
          where: { id: job.id },
          data: {
            paymentStatus: 'paid',
            paidAt: new Date(),
          },
        })

        console.log(`Payment intent succeeded for job ${job.id}`, {
          jobId: job.id,
          paymentIntentId: paymentIntent.id,
        })
      }
    }

    return NextResponse.json({ received: true })
  } catch (error) {
    logger.error('Webhook handler error', {
      error: String(error),
      eventType: event?.type,
    })
    return NextResponse.json(
      { error: 'Webhook handler failed' },
      { status: 500 }
    )
  }
}

