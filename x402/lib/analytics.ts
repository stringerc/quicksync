/**
 * Analytics utility - Plausible integration
 * No-ops if PLAUSIBLE_DOMAIN is not set (privacy-safe)
 */

declare global {
  interface Window {
    plausible?: (event: string, options?: { props?: Record<string, string | number> }) => void
  }
}

export function trackEvent(eventName: string, props?: Record<string, string | number>) {
  if (typeof window === 'undefined') return // Server-side safety

  const domain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN
  if (!domain) return // No tracking if not configured

  // Plausible script should be loaded in layout.tsx
  if (window.plausible) {
    window.plausible(eventName, { props })
  } else {
    // Fallback: log to console in dev
    if (process.env.NODE_ENV === 'development') {
      console.log('[Analytics]', eventName, props)
    }
  }
}

// Convenience functions for common events
export const analytics = {
  uploadStarted: () => trackEvent('upload_started'),
  uploadCompleted: (jobId: string) => trackEvent('upload_completed', { jobId }),
  jobReady: (jobId: string, confidenceScore?: number) =>
    trackEvent('job_ready', { jobId, confidenceScore: confidenceScore || 0 }),
  checkoutStarted: (jobId: string, type: 'single' | 'credit_pack') =>
    trackEvent('checkout_started', { jobId, type }),
  paidConfirmed: (jobId: string, type: 'single' | 'credit') =>
    trackEvent('paid_confirmed', { jobId, type }),
  creditPackPurchased: () => trackEvent('credit_pack_purchased'),
  downloadCompleted: (jobId: string, format: 'csv' | 'qbo') =>
    trackEvent('download_completed', { jobId, format }),
  parseFailed: (jobId: string) => trackEvent('parse_failed', { jobId }),
}

