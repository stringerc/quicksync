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
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="mb-6 flex justify-between items-center">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                QuickSync
              </h1>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Logout
              </button>
            </div>
            <UploadForm token={token!} />
          </div>
        </div>
      </main>
    )
  }

  // Landing page (unauthenticated)
  return (
    <main className="min-h-screen bg-white">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 lg:py-32">
          <div className="text-center animate-fade-in-up">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Turn PDFs into
              <span className="block mt-2 bg-gradient-to-r from-yellow-200 to-pink-200 bg-clip-text text-transparent">
                QuickBooks-ready files
              </span>
            </h1>
            <p className="text-xl sm:text-2xl text-purple-100 mb-8 max-w-3xl mx-auto">
              Upload your bank or credit card statement. Get clean CSV or QBO files in minutes.
              <span className="block mt-2 text-lg text-purple-200">Preview before you pay. No cleanup needed.</span>
            </p>

            {/* Upload CTA */}
            <div className="mb-12 max-w-2xl mx-auto">
              <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 sm:p-8 border border-white/20">
                <UploadForm token={token} />
              </div>
            </div>

            {/* Trust indicators */}
            <div className="flex flex-wrap justify-center gap-6 text-sm text-purple-200">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Preview first</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Secure & private</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
                <span>Fast processing</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 sm:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Everything you need
            </h2>
            <p className="text-xl text-gray-600">
              Professional-grade conversion in three simple steps
            </p>
          </div>

          <div className="grid sm:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-2xl shadow-lg hover-lift">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">1. Upload PDF</h3>
              <p className="text-gray-600 leading-relaxed">
                Drag and drop or select your bank or credit card statement PDF.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg hover-lift">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">2. Preview results</h3>
              <p className="text-gray-600 leading-relaxed">
                Review extracted data, validation summary, and confidence score before paying.
              </p>
            </div>

            <div className="bg-white p-8 rounded-2xl shadow-lg hover-lift">
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">3. Download files</h3>
              <p className="text-gray-600 leading-relaxed">
                Get both CSV and QBO formats. Ready to import into QuickBooks or Excel.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Simple, transparent pricing
            </h2>
            <p className="text-xl text-gray-600">
              Pay per file, or save with a credit pack
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="bg-white p-8 rounded-2xl border-2 border-gray-200 hover-lift">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Single file</h3>
              <div className="mb-4">
                <span className="text-5xl font-bold text-gray-900">$9</span>
                <span className="text-gray-600 ml-2">per conversion</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-700">
                  <svg className="w-5 h-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  CSV + QBO files included
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="w-5 h-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Validation summary
                </li>
                <li className="flex items-center text-gray-700">
                  <svg className="w-5 h-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Preview before payment
                </li>
              </ul>
            </div>

            <div className="bg-gradient-to-br from-purple-600 to-blue-600 p-8 rounded-2xl text-white relative overflow-hidden hover-lift">
              <div className="absolute top-4 right-4">
                <span className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-semibold">
                  POPULAR
                </span>
              </div>
              <h3 className="text-2xl font-bold mb-2">Pack of 10</h3>
              <div className="mb-4">
                <span className="text-5xl font-bold">$29</span>
                <span className="text-purple-100 ml-2">save $61</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-yellow-300 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  10 file conversions
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-yellow-300 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Use credits anytime
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-yellow-300 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Best value
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="py-16 sm:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid sm:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Secure & Private</h3>
              <p className="text-gray-600">Your files are encrypted and automatically deleted after 30 days.</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Fast Processing</h3>
              <p className="text-gray-600">Get your files in minutes, not hours. No waiting around.</p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Accuracy Guaranteed</h3>
              <p className="text-gray-600">Confidence scoring and validation ensure high-quality results.</p>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="py-16 sm:py-24 bg-white">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Frequently asked questions
            </h2>
          </div>

          <div className="space-y-4">
            {[
              {
                q: 'What file formats do you support?',
                a: 'We support PDF files with selectable text. Scanned PDFs or images are not currently supported.',
              },
              {
                q: 'How accurate is the extraction?',
                a: 'Each file receives a confidence score. If the score is below 70%, we mark it for review and recommend you don\'t pay until we verify the results.',
              },
              {
                q: 'Is my data secure?',
                a: 'Yes. Files are stored privately and securely. We never sell your data. Files are automatically deleted after 30 days.',
              },
              {
                q: 'What if the extraction fails?',
                a: 'If parsing fails or confidence is too low, we won\'t ask you to pay. You can request a manual review or try uploading again.',
              },
              {
                q: 'Do you offer refunds?',
                a: 'Yes. If you\'re not satisfied with the results, contact support within 7 days for a full refund.',
              },
            ].map((faq, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-6 hover:bg-gray-100 transition-colors">
                <h3 className="font-bold text-lg text-gray-900 mb-2">{faq.q}</h3>
                <p className="text-gray-600">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Login Section (if not authenticated) */}
      {!isAuthenticated && (
        <div className="py-12 bg-gray-50 border-t">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white rounded-2xl p-8 shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-2 text-center">
                Already have an account?
              </h3>
              <p className="text-gray-600 mb-6 text-center">
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
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                    placeholder="you@example.com"
                    onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                  />
                </div>
                <button
                  onClick={handleLogin}
                  className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-6 rounded-lg hover:from-purple-700 hover:to-blue-700 transition font-semibold shadow-lg"
                >
                  Send Magic Link
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-sm">
            <strong className="text-gray-300">Data handling:</strong> Files are stored privately and securely. Automatic deletion after 30 days.
            We never sell or share your data. Payments processed securely via Stripe.
          </p>
        </div>
      </footer>

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
