import Stripe from 'stripe'

// Initialize Stripe - will throw at runtime if STRIPE_SECRET_KEY is not set
// We allow build to proceed without the key (it will fail when stripe is actually used)
const stripeKey = process.env.STRIPE_SECRET_KEY || ''
if (!stripeKey && process.env.NODE_ENV !== 'test') {
  console.warn('Warning: STRIPE_SECRET_KEY is not set. Stripe operations will fail at runtime.')
}

export const stripe = stripeKey 
  ? new Stripe(stripeKey, {
      apiVersion: '2023-10-16',
    })
  : null as any // Type assertion to allow build - will fail at runtime if used without key

export const PRICE_PER_FILE = parseInt(process.env.PRICE_PER_FILE || '900') // $9.00 in cents
export const PRICE_PACK_10 = parseInt(process.env.PRICE_PACK_10 || '2900') // $29.00 in cents

