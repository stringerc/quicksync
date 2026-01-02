'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import UploadForm from '@/components/UploadForm'

export default function BookkeepersPage() {
  const [token, setToken] = useState<string | null>(null)
  const [email, setEmail] = useState<string>('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const urlToken = urlParams.get('token')
    
    if (urlToken) {
      localStorage.setItem('auth_token', urlToken)
      setToken(urlToken)
      setIsAuthenticated(true)
      window.history.replaceState({}, '', '/bookkeepers')
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

  // Authenticated view
  if (isAuthenticated) {
    return (
      <main className="min-h-screen p-8 max-w-6xl mx-auto">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">For Bookkeepers & Firms</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Logout
          </button>
        </div>

        <UploadForm token={token} />
      </main>
    )
  }

  // Landing page for bookkeepers
  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-8 py-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Convert client PDFs into import-ready files.
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Upload a sample file and get a clean import-ready output. If it fails, you don&apos;t pay.
          </p>

          {/* Login/Upload CTA */}
          <div className="bg-gray-50 rounded-lg p-6 mb-12 max-w-2xl">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">Get started</h2>
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
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition font-semibold"
              >
                Send Magic Link to Upload
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Key Benefits for Bookkeepers */}
      <div className="max-w-6xl mx-auto px-8 py-16">
        <h2 className="text-3xl font-bold text-gray-900 mb-8">Perfect for bookkeeping firms</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">No risk trial</h3>
            <p className="text-gray-600">Preview results before payment. If parsing fails or needs review, don&apos;t pay.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">QuickBooks ready</h3>
            <p className="text-gray-600">Get QBO files that import directly into QuickBooks. No manual data entry.</p>
          </div>
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="font-semibold text-lg mb-2">Client-ready CSV</h3>
            <p className="text-gray-600">Clean, validated CSV files you can share with clients or import anywhere.</p>
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
              <h3 className="font-semibold text-lg mb-2">Upload client PDF</h3>
              <p className="text-gray-600">Upload a bank or credit card statement PDF.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">2</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Review results</h3>
              <p className="text-gray-600">Check the confidence score and validation summary. If it needs review, don&apos;t pay.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">3</span>
              </div>
              <h3 className="font-semibold text-lg mb-2">Download & import</h3>
              <p className="text-gray-600">If results look good, download CSV or QBO and import into QuickBooks.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing for Firms */}
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
              <div className="text-sm font-semibold text-blue-600 mb-2">BEST VALUE</div>
              <h3 className="text-2xl font-bold mb-2">Pack of 10</h3>
              <div className="text-4xl font-bold text-gray-900 mb-4">$29</div>
              <p className="text-gray-600 mb-6">Save $61 - Use anytime</p>
              <ul className="space-y-2 text-gray-700">
                <li>✓ 10 file conversions</li>
                <li>✓ Use credits anytime</li>
                <li>✓ Perfect for multiple clients</li>
              </ul>
            </div>
          </div>
          <p className="text-center text-gray-600 mt-8 text-sm">
            <strong>Firm pack coming soon:</strong> Bulk processing for larger firms with multiple clients.
          </p>
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
    </main>
  )
}

