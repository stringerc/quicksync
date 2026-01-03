import { prisma } from './db'

/**
 * Get user's credit balance
 */
export async function getCreditBalance(userId: string): Promise<number> {
  const credit = await prisma.credit.findUnique({
    where: { userId },
  })
  return credit?.balance || 0
}

/**
 * Add credits to user account
 */
export async function addCredits(userId: string, amount: number, source: string = 'purchase'): Promise<void> {
  await prisma.credit.upsert({
    where: { userId },
    create: {
      userId,
      balance: amount,
      source,
    },
    update: {
      balance: {
        increment: amount,
      },
    },
  })
}

/**
 * Redeem one credit (atomic operation)
 * Returns true if credit was redeemed, false if insufficient balance
 */
export async function redeemCredit(userId: string): Promise<boolean> {
  try {
    const result = await prisma.$transaction(async (tx) => {
      const credit = await tx.credit.findUnique({
        where: { userId },
      })

      const currentBalance = credit?.balance || 0
      if (currentBalance < 1) {
        return false
      }

      await tx.credit.update({
        where: { userId },
        data: {
          balance: {
            decrement: 1,
          },
        },
      })

      return true
    })

    return result
  } catch (error) {
    console.error('Credit redemption error:', error)
    return false
  }
}

