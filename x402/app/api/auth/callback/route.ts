import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { generateAuthToken } from '@/lib/auth'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const token = searchParams.get('token')

  if (!token) {
    return NextResponse.json({ error: 'Token required' }, { status: 400 })
  }

  try {
    const user = await prisma.user.findFirst({
      where: {
        magicLinkToken: token,
        magicLinkExpires: {
          gt: new Date(),
        },
      },
    })

    if (!user) {
      return NextResponse.json({ error: 'Invalid or expired token' }, { status: 401 })
    }

    // Clear magic link token
    await prisma.user.update({
      where: { id: user.id },
      data: {
        magicLinkToken: null,
        magicLinkExpires: null,
      },
    })

    // Generate auth token
    const authToken = generateAuthToken(user.id, user.email)

    // Check if this is a new user (created less than 1 minute ago) and send welcome email
    try {
      const isNewUser = user.createdAt && (Date.now() - user.createdAt.getTime() < 60000) // Created < 1 min ago
      if (isNewUser) {
        const { sendWelcomeEmail } = await import('@/lib/email')
        await sendWelcomeEmail(user.email).catch((err) => {
          // Don't fail auth if email fails
          console.error('Failed to send welcome email:', err)
        })
      }
    } catch (emailError) {
      // Don't fail auth if email fails
      console.error('Welcome email error:', emailError)
    }

    // Redirect to home with token (in production, set as HTTP-only cookie)
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'
    const response = NextResponse.redirect(`${appUrl}/?token=${authToken}`)

    // Set cookie (for production)
    response.cookies.set('auth_token', authToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
    })

    return response
  } catch (error) {
    console.error('Auth callback error:', error)
    return NextResponse.json(
      { error: 'Authentication failed' },
      { status: 500 }
    )
  }
}

