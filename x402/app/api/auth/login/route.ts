import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { generateMagicLinkToken, generateAuthToken } from '@/lib/auth'
import nodemailer from 'nodemailer'

export const dynamic = 'force-dynamic'

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json()

    if (!email || !email.includes('@')) {
      return NextResponse.json({ error: 'Valid email required' }, { status: 400 })
    }

    // Get or create user
    let user = await prisma.user.findUnique({
      where: { email },
    })

    if (!user) {
      user = await prisma.user.create({
        data: { email },
      })
    }

    // Generate magic link token
    const token = generateMagicLinkToken()
    const expiresAt = new Date()
    expiresAt.setHours(expiresAt.getHours() + 1) // 1 hour expiry

    await prisma.user.update({
      where: { id: user.id },
      data: {
        magicLinkToken: token,
        magicLinkExpires: expiresAt,
      },
    })

    // Send magic link email
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'
    const magicLink = `${appUrl}/auth/callback?token=${token}`

    // Configure email (using nodemailer - configure SMTP in .env)
    if (process.env.SMTP_HOST) {
      const transporter = nodemailer.createTransport({
        host: process.env.SMTP_HOST,
        port: parseInt(process.env.SMTP_PORT || '587'),
        secure: false,
        auth: {
          user: process.env.SMTP_USER,
          pass: process.env.SMTP_PASS,
        },
      })

      await transporter.sendMail({
        from: process.env.SMTP_USER,
        to: email,
        subject: 'Your magic link to PDF Converter',
        html: `
          <p>Click the link below to sign in:</p>
          <p><a href="${magicLink}">${magicLink}</a></p>
          <p>This link expires in 1 hour.</p>
        `,
      })
    } else {
      // Development: log the link
      console.log('Magic link (dev mode):', magicLink)
    }

    return NextResponse.json({
      message: 'Magic link sent to your email',
      // In development, return the link
      ...(process.env.NODE_ENV === 'development' && { magicLink }),
    })
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { error: 'Failed to send magic link' },
      { status: 500 }
    )
  }
}

