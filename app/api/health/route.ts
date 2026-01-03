import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Basic health check - no database or external service calls
    const health = {
      ok: true,
      timestamp: new Date().toISOString(),
      version: process.env.VERCEL_GIT_COMMIT_SHA || 'dev',
      environment: process.env.NODE_ENV || 'development',
    }

    return NextResponse.json(health, { status: 200 })
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        error: String(error),
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    )
  }
}

