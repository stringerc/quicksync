'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import UploadForm from '@/components/UploadForm'

export default function Home() {
  const [token, setToken] = useState<string | null>(null)
  const [email, setEmail] = useState<string>('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Check for token in URL or cookie
    const urlParams = new URLSearchParams(window.location.search)
    const urlToken = urlParams.get('token')
    
    if (urlToken) {
      localStorage.setItem('auth_token', urlToken)
      setToken(urlToken)
      setIsAuthenticated(true)
      window.history.replaceState({}, '', '/')
    } else {
      const storedToken = localStorage.getItem('auth_token')
      if (storedToken) {
        setToken(storedToken)
        setIsAuthenticated(true)
      }
    }
  }, [])

  const handleLogin = async () => {
    if (!email) return

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()
      
      if (response.ok) {
        alert('Check your email for the magic link!' + (data.magicLink ? `\n\nDev link: ${data.magicLink}` : ''))
      } else {
        alert('Failed to send magic link: ' + data.error)
      }
    } catch (error) {
      console.error('Login error:', error)
      alert('Failed to send magic link')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setIsAuthenticated(false)
    setEmail('')
  }

  // Authenticated view - show upload interface
  if (isAuthenticated) {
    return (
      <main className="min-h-screen p-8 max-w-6xl mx-auto">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">PDF to CSV Converter</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Logout
          </button>
        </div>

        <UploadForm token={token!} />
      </main>
    )
  }

  // Landing page (unauthenticated)
  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-8 py-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Turn bank/credit card PDFs into clean QuickBooks-ready files in minutes.
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Upload a statement. Get a validated CSV or QBO you can import. No manual cleanup needed.
          </p>

          {/* Upload CTA - No login required */}
          <div className="mb-12 max-w-2xl">
            <UploadForm token={token} />
          </div>

          {/* Optional login section */}
          {!isAuthenticated && (
            <div className="bg-gray-50 rounded-lg p-6 mb-12 max-w-2xl">
              <h3 className="text-md font-semibold mb-2 text-gray-800">Already have an account?</h3>
              <p className="text-sm text-gray-600 mb-4">
                Log in to track all your conversions and manage credits.
              </p>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="you@example.com"
                    onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                  />
                </div>
                <button
                  onClick={handleLogin}
                  className="w-full bg-gray-600 text-white py-2 px-6 rounded-lg hover:bg-gray-700 transition font-semibold"
                >
                  Send Magic Link
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* What You Get */}
      <div className="max-w-6xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">What you get</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">CSV + QBO files</h3>
            <p className="text-gray-600">Both formats included. Ready to import into QuickBooks or Excel.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">Validation summary</h3>
            <p className="text-gray-600">See row count, date range, totals, and confidence score before downloading.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">Pay only when ready</h3>
            <p className="text-gray-600">Preview your results first. Only pay when you&apos;re ready to download.</p>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-white border-y">
        <div className="max-w-6xl mx-auto px-8 py-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">How it works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">1</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Upload PDF</h3>
              <p className="text-gray-600">Upload your bank or credit card statement PDF.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">2</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Preview summary</h3>
              <p className="text-gray-600">Review the extracted data, confidence score, and validation summary.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">3</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Pay & download</h3>
              <p className="text-gray-600">If the results look good, pay and download your CSV or QBO file.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Supported Documents */}
      <div className="max-w-6xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">Supported documents</h2>
        <div className="bg-white p-6 rounded-lg border">
          <p className="text-gray-700 mb-4">
            We currently support text-based PDF statements from:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-600">
            <li>Bank statements (Chase, Bank of America, Wells Fargo, etc.)</li>
            <li>Credit card statements (Visa, Mastercard, Amex, etc.)</li>
            <li>Payout reports from payment processors</li>
          </ul>
          <p className="text-gray-600 mt-4 text-sm">
            <strong>Note:</strong> Scanned PDFs or images are not currently supported. The PDF must contain selectable text.
          </p>
        </div>
      </div>

      {/* Pricing */}
      <div className="bg-gray-50 border-y">
        <div className="max-w-6xl mx-auto px-8 py-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Pricing</h2>
          <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
            <div className="bg-white p-8 rounded-lg border-2">
              <h3 className="text-2xl font-bold mb-2">Single file</h3>
              <div className="text-4xl font-bold text-gray-900 mb-4">$9</div>
              <p className="text-gray-600 mb-6">Per conversion</p>
              <ul className="space-y-2 text-gray-700">
                <li>✓ CSV + QBO files</li>
                <li>✓ Validation summary</li>
                <li>✓ Preview before payment</li>
              </ul>
            </div>
            <div className="bg-white p-8 rounded-lg border-2 border-blue-500">
              <div className="text-sm font-semibold text-blue-600 mb-2">POPULAR</div>
              <h3 className="text-2xl font-bold mb-2">Pack of 10</h3>
              <div className="text-4xl font-bold text-gray-900 mb-4">$29</div>
              <p className="text-gray-600 mb-6">Save $61</p>
              <ul className="space-y-2 text-gray-700">
                <li>✓ 10 file conversions</li>
                <li>✓ Use credits anytime</li>
                <li>✓ Best value</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="max-w-3xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">Frequently asked questions</h2>
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">What file formats do you support?</h3>
            <p className="text-gray-600">We support PDF files with selectable text. Scanned PDFs or images are not currently supported.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">How accurate is the extraction?</h3>
            <p className="text-gray-600">Each file receives a confidence score. If the score is below 70%, we mark it for review and recommend you don&apos;t pay until we verify the results.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">Is my data secure?</h3>
            <p className="text-gray-600">Yes. Files are stored privately and securely. We never sell your data. Files are automatically deleted after 30 days.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">What if the extraction fails?</h3>
            <p className="text-gray-600">If parsing fails or confidence is too low, we won&apos;t ask you to pay. You can request a manual review or try uploading again.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">Do you offer refunds?</h3>
            <p className="text-gray-600">Yes. If you&apos;re not satisfied with the results, contact support within 7 days for a full refund.</p>
          </div>
        </div>
      </div>

      {/* Data Handling */}
      <div className="bg-gray-100 border-t">
        <div className="max-w-3xl mx-auto px-8 py-8">
          <p className="text-sm text-gray-600 text-center">
            <strong>Data handling:</strong> Files are stored privately and securely. Automatic deletion after 30 days. 
            We never sell or share your data. Payments processed securely via Stripe.
          </p>
        </div>
      </div>

      {/* Structured Data for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'SoftwareApplication',
            name: 'QuickSync',
            applicationCategory: 'BusinessApplication',
            operatingSystem: 'Web',
            offers: {
              '@type': 'Offer',
              price: '9.00',
              priceCurrency: 'USD',
            },
            aggregateRating: {
              '@type': 'AggregateRating',
              // Will add when we have reviews
            },
            description: 'Convert bank and credit card statement PDFs into clean CSV or QBO files for QuickBooks import.',
            url: process.env.NEXT_PUBLIC_APP_URL || 'https://quicksync.app',
          }),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'Organization',
            name: 'QuickSync',
            url: process.env.NEXT_PUBLIC_APP_URL || 'https://quicksync.app',
            logo: `${process.env.NEXT_PUBLIC_APP_URL || 'https://quicksync.app'}/logo.png`,
            description: 'Bank statement to CSV/QBO converter for QuickBooks import',
          }),
        }}
      />
    </main>
  )
}
