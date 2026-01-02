import { NextRequest, NextResponse } from 'next/server'
import { stripe, PRICE_PACK_10 } from '@/lib/stripe'
import { prisma } from '@/lib/db'
import { getCurrentUser } from '@/lib/auth'
import { logger } from '@/lib/logger'

export async function POST(request: NextRequest) {
  let user: any = null
  
  try {
    const authHeader = request.headers.get('authorization')
    user = await getCurrentUser(authHeader)

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'

    // Create Stripe Checkout session for credit pack
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: 'Pack of 10 File Conversions',
              description: '10 credits for PDF to CSV/QBO conversions',
            },
            unit_amount: PRICE_PACK_10,
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${appUrl}/?credits=purchased`,
      cancel_url: `${appUrl}/?credits=canceled`,
      metadata: {
        purchaseType: 'credit_pack',
        userId: user.id,
        credits: '10',
      },
    })

    logger.info('Credit pack checkout created', {
      userId: user.id,
      sessionId: session.id,
    })

    return NextResponse.json({
      sessionId: session.id,
      url: session.url,
    })
  } catch (error) {
    logger.error('Credit pack checkout error', {
      error: String(error),
      userId: user?.id,
    })
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    )
  }
}

