import type { Metadata } from 'next'
import './globals.css'
import Script from 'next/script'

export const metadata: Metadata = {
  title: {
    default: 'QuickSync - Bank Statement to CSV/QBO Converter | QuickBooks Ready',
    template: '%s | QuickSync',
  },
  description: 'Convert bank and credit card statement PDFs into clean CSV or QBO files for QuickBooks import. Fast, accurate, and secure. Preview before you pay.',
  keywords: ['bank statement converter', 'PDF to CSV', 'PDF to QBO', 'QuickBooks import', 'bank statement to CSV', 'statement converter'],
  authors: [{ name: 'QuickSync' }],
  creator: 'QuickSync',
  publisher: 'QuickSync',
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'https://quicksync.app'),
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: process.env.NEXT_PUBLIC_APP_URL || 'https://quicksync.app',
    siteName: 'QuickSync',
    title: 'QuickSync - Bank Statement to CSV/QBO Converter',
    description: 'Convert bank and credit card statement PDFs into clean CSV or QBO files for QuickBooks import. Fast, accurate, and secure.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'QuickSync - Bank Statement to CSV/QBO Converter',
    description: 'Convert bank and credit card statement PDFs into clean CSV or QBO files for QuickBooks import.',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    // Add Google Search Console verification when available
    // google: 'verification-code-here',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const plausibleDomain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN

  return (
    <html lang="en">
      {plausibleDomain && (
        <Script
          defer
          data-domain={plausibleDomain}
          src="https://plausible.io/js/script.js"
        />
      )}
      <body>{children}</body>
    </html>
  )
}

