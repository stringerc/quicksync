import jwt from 'jsonwebtoken'
import crypto from 'crypto'
import { prisma } from './db'

const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production'

export interface AuthToken {
  userId: string
  email: string
}

/**
 * Generate magic link token
 */
export function generateMagicLinkToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

/**
 * Generate JWT for authenticated user
 */
export function generateAuthToken(userId: string, email: string): string {
  return jwt.sign({ userId, email }, JWT_SECRET, { expiresIn: '7d' })
}

/**
 * Verify JWT token
 */
export function verifyAuthToken(token: string): AuthToken | null {
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as AuthToken
    return decoded
  } catch {
    return null
  }
}

/**
 * Get user from request (from cookie or header)
 */
export async function getCurrentUser(
  authHeader: string | null
): Promise<{ id: string; email: string } | null> {
  if (!authHeader) return null

  const token = authHeader.replace('Bearer ', '')
  const payload = verifyAuthToken(token)

  if (!payload) return null

  const user = await prisma.user.findUnique({
    where: { id: payload.userId },
  })

  if (!user) return null

  return { id: user.id, email: user.email }
}

