/**
 * Free First File utility
 * Tracks and checks if a user is eligible for their free first file
 */

import { prisma } from './db'

/**
 * Check if a user is eligible for free first file
 * Returns true if user has never paid for a job before
 */
export async function isEligibleForFreeFirstFile(userId: string): Promise<boolean> {
  // Check if user has any paid jobs
  const paidJob = await prisma.job.findFirst({
    where: {
      userId,
      paymentStatus: 'paid',
    },
  })

  // Also check if user has redeemed any credits (counts as payment)
  const creditRedeemedJob = await prisma.job.findFirst({
    where: {
      userId,
      creditRedeemedAt: {
        not: null,
      },
    },
  })

  // User is eligible if they have no paid jobs and no credit-redemeed jobs
  return !paidJob && !creditRedeemedJob
}

/**
 * Check if an email (for anonymous users) is eligible for free first file
 * This checks if the email has been used for any paid jobs
 */
export async function isEmailEligibleForFreeFirstFile(email: string): Promise<boolean> {
  // Find user by email
  const user = await prisma.user.findUnique({
    where: { email },
  })

  if (!user) {
    // New email = eligible for free file
    return true
  }

  // Check if user has any paid jobs
  return isEligibleForFreeFirstFile(user.id)
}

