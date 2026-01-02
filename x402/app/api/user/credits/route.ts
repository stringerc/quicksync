import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
import { getCurrentUser } from '@/lib/auth'
import { getCreditBalance } from '@/lib/credits'

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    const user = await getCurrentUser(authHeader)

    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const balance = await getCreditBalance(user.id)

    return NextResponse.json({ balance })
  } catch (error) {
    console.error('Get credits error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch credits' },
      { status: 500 }
    )
  }
}

