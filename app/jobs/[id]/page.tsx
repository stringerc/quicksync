'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { analytics } from '@/lib/analytics'

interface Job {
  id: string
  fileName: string
  status: string
  paymentStatus: string
  createdAt: string
  processedAt?: string
  paidAt?: string
  creditRedeemedAt?: string
  reviewRequestedAt?: string
  rowCount?: number
  dateRangeStart?: string
  dateRangeEnd?: string
  totalDebit?: string
  totalCredit?: string
  totalBalance?: string
  confidenceScore?: number
  csvFilePath?: string
  qboFilePath?: string
  previewCsvFilePath?: string
  previewQboFilePath?: string
  creditBalance?: number
  sampleRows?: string[][] // Sample CSV rows for preview
}

export default function JobPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = params.id as string

  const [token, setToken] = useState<string | null>(null)
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [requestingReview, setRequestingReview] = useState(false)
  const [paymentEmail, setPaymentEmail] = useState<string>('')
  const [showEmailInput, setShowEmailInput] = useState(false)

  useEffect(() => {
    // Check for token (optional - user might not be logged in)
    const storedToken = localStorage.getItem('auth_token')
    if (storedToken) {
      setToken(storedToken)
    }
    fetchJob()
    // Auto-refresh if processing
    const interval = setInterval(() => {
      if (job?.status === 'processing' || job?.status === 'pending') {
        fetchJob()
      }
    }, 3000) // Poll every 3 seconds if processing
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId])

  const fetchJob = async () => {
    try {
      const storedToken = localStorage.getItem('auth_token')
      const headers: HeadersInit = {}
      if (storedToken) {
        headers.Authorization = `Bearer ${storedToken}`
      }

      const response = await fetch(`/api/jobs/${jobId}`, {
        headers,
      })

      if (response.ok) {
        const data = await response.json()
        setJob(data)

        // Auto-trigger processing if pending
        if (data.status === 'pending' && !processing) {
          handleProcess()
        }

        // Check if payment was just completed
        if (searchParams.get('payment') === 'success' && data.paymentStatus === 'paid' && data.status === 'pending') {
          handleProcess()
        }
      } else {
        if (response.status === 404) {
          // Job not found - show error
        } else {
          console.error('Failed to fetch job:', response.status)
        }
      }
    } catch (error) {
      console.error('Fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePayment = async () => {
    // If no email provided, show email input first
    if (!paymentEmail && !token) {
      setShowEmailInput(true)
      return
    }

    setCheckoutLoading(true)
    analytics.checkoutStarted(jobId, 'single')

    try {
      const storedToken = localStorage.getItem('auth_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (storedToken) {
        headers.Authorization = `Bearer ${storedToken}`
      }

      const response = await fetch('/api/payment/create-checkout', {
        method: 'POST',
        headers,
        body: JSON.stringify({ 
          jobId,
          email: paymentEmail || undefined, // Include email for anonymous users
        }),
      })

      const data = await response.json()

      if (response.ok) {
        if (data.free) {
          // Free first file - refresh page to show updated status
          alert('🎉 Free first file! Your job is ready for download.')
          fetchJob()
        } else if (data.url) {
          // Redirect to Stripe checkout
          window.location.href = data.url
        } else {
          alert('Unexpected response: ' + JSON.stringify(data))
          setCheckoutLoading(false)
        }
      } else {
        alert('Failed to create checkout: ' + data.error)
        setCheckoutLoading(false)
      }
    } catch (error) {
      console.error('Payment error:', error)
      alert('Failed to create checkout')
      setCheckoutLoading(false)
    }
  }

  const handleProcess = async () => {
    if (processing) return

    setProcessing(true)

    try {
      const storedToken = localStorage.getItem('auth_token')
      const sessionId = localStorage.getItem(`job_${jobId}_session`)
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (storedToken) {
        headers.Authorization = `Bearer ${storedToken}`
      }

      const response = await fetch('/api/process', {
        method: 'POST',
        headers,
        body: JSON.stringify({ jobId, sessionId }),
      })

      const data = await response.json()

      if (response.ok) {
        // Refresh job data
        setTimeout(() => {
          fetchJob()
          setProcessing(false)
        }, 2000)
      } else {
        alert('Processing failed: ' + data.error)
        setProcessing(false)
      }
    } catch (error) {
      console.error('Process error:', error)
      alert('Processing failed')
      setProcessing(false)
    }
  }

  const handleRequestReview = async () => {
    if (!token) {
      alert('Please log in to request a review')
      return
    }

    setRequestingReview(true)

    try {
      const response = await fetch(`/api/jobs/${jobId}/request-review`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.ok) {
        alert('Review requested. Our team will look into this.')
        fetchJob()
      } else {
        alert('Failed to request review')
      }
    } catch (error) {
      console.error('Request review error:', error)
      alert('Failed to request review')
    } finally {
      setRequestingReview(false)
    }
  }

  const handleDownload = async (format: 'csv' | 'qbo') => {
    // Download requires auth - redirect to payment if not authenticated
    if (!token && job?.paymentStatus !== 'paid') {
      setShowEmailInput(true)
      return
    }

    const storedToken = localStorage.getItem('auth_token')
    if (!storedToken && job?.paymentStatus !== 'paid') {
      alert('Please complete payment to download')
      return
    }

    const url = `/api/download/${jobId}/${format}`
    
    try {
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Download failed')
      }

      const blob = await response.blob()
      const blobUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = `${job?.fileName.replace('.pdf', '') || 'output'}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(blobUrl)

      analytics.downloadCompleted(jobId, format)

      // Refresh to update credit balance
      fetchJob()
    } catch (error) {
      console.error('Download error:', error)
      alert('Download failed: ' + (error instanceof Error ? error.message : 'Unknown error'))
    }
  }

  const handlePreview = (format: 'csv' | 'qbo') => {
    // Open preview in new tab
    const previewUrl = `/api/preview/${jobId}/${format}`
    window.open(previewUrl, '_blank')
  }

  if (loading) {
    return (
      <main className="min-h-screen p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto">
        <div className="text-center">Loading...</div>
      </main>
    )
  }

  if (!job) {
    return (
      <main className="min-h-screen p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="text-center text-red-600 mb-4">Job not found</div>
          <div className="flex items-center justify-center gap-2">
            <span className="text-sm text-gray-600">Support token:</span>
            <code className="px-2 py-1 bg-gray-100 rounded text-sm font-mono">{jobId}</code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(jobId)
                alert('Support token copied to clipboard!')
              }}
              className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
            >
              Copy
            </button>
          </div>
        </div>
      </main>
    )
  }

  const isPaid = job.paymentStatus === 'paid' && job.paidAt
  const hasCredits = (job.creditBalance || 0) >= 1
  const isCompleted = job.status === 'completed' || job.status === 'needs_review'
  const isFailed = job.status === 'failed'
  const needsReview = job.status === 'needs_review' || (job.confidenceScore !== undefined && job.confidenceScore < 70)
  const canDownload = isPaid || hasCredits
  const shouldBlockPayment = isFailed || needsReview
  const hasPreview = isCompleted && (job.previewCsvFilePath || job.previewQboFilePath)

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <button
        onClick={() => router.push('/')}
        className="mb-4 text-blue-600 hover:text-blue-800"
      >
        ← Back to Home
      </button>

      <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 mb-4 sm:mb-6">
        <h1 className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4 text-gray-800 break-words">{job.fileName}</h1>

        <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-4 sm:mb-6">
          <div>
            <div className="text-sm text-gray-600">Status</div>
            <div className="font-semibold capitalize">{job.status}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Payment</div>
            <div className="font-semibold capitalize">{job.paymentStatus}</div>
          </div>
        </div>

        {/* Credit balance display */}
        {token && (job.creditBalance || 0) > 0 && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm text-gray-700">
              <strong>Credits available:</strong> {job.creditBalance}
            </div>
          </div>
        )}

        {/* Email input for anonymous payment */}
        {showEmailInput && !token && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 mb-2 font-semibold">Enter your email to continue</p>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="email"
                value={paymentEmail}
                onChange={(e) => setPaymentEmail(e.target.value)}
                placeholder="your@email.com"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-base sm:text-sm"
              />
              <div className="flex gap-2">
                <button
                  onClick={handlePayment}
                  disabled={!paymentEmail || checkoutLoading}
                  className="flex-1 sm:flex-initial bg-green-600 text-white py-2 px-4 sm:px-6 rounded-lg hover:bg-green-700 disabled:bg-gray-400 text-sm sm:text-base"
                >
                  Continue
                </button>
                <button
                  onClick={() => setShowEmailInput(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm sm:text-base"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* B3: Block payment for failed or needs_review */}
        {shouldBlockPayment && !isPaid && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800 font-semibold mb-2">
              {isFailed ? 'This file failed to process.' : 'This file needs review before payment.'}
            </p>
            <p className="text-yellow-700 text-sm mb-4">
              Don&apos;t pay yet. Please review the results or request a manual review.
            </p>
            {token && (
              <button
                onClick={handleRequestReview}
                disabled={requestingReview || job.reviewRequestedAt !== undefined}
                className="bg-yellow-600 text-white py-2 px-6 rounded-lg hover:bg-yellow-700 disabled:bg-gray-400"
              >
                {job.reviewRequestedAt ? 'Review Requested' : requestingReview ? 'Requesting...' : 'Request Manual Review'}
              </button>
            )}
          </div>
        )}

        {/* Preview section - shown when processing is complete */}
        {hasPreview && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-semibold text-green-800 mb-2">Preview Your Results</h3>
            <p className="text-green-700 text-sm mb-4">
              Review your converted files with watermarks. Pay to download clean versions.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
              {job.previewCsvFilePath && (
                <button
                  onClick={() => handlePreview('csv')}
                  className="bg-blue-600 text-white py-2.5 px-6 rounded-lg hover:bg-blue-700 text-sm sm:text-base"
                >
                  Preview CSV
                </button>
              )}
              {job.previewQboFilePath && (
                <button
                  onClick={() => handlePreview('qbo')}
                  className="bg-purple-600 text-white py-2.5 px-6 rounded-lg hover:bg-purple-700 text-sm sm:text-base"
                >
                  Preview QBO
                </button>
              )}
            </div>
          </div>
        )}

        {/* Payment options (only if not blocked) */}
        {!shouldBlockPayment && !isPaid && !hasCredits && isCompleted && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800 mb-4">
              Payment required to download clean files.
            </p>
            <button
              onClick={handlePayment}
              disabled={checkoutLoading}
              className="bg-green-600 text-white py-2 px-6 rounded-lg hover:bg-green-700 disabled:bg-gray-400"
            >
              {checkoutLoading ? 'Loading...' : 'Pay $9 to Download'}
            </button>
          </div>
        )}

        {/* Credit download option */}
        {!isPaid && hasCredits && isCompleted && token && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 mb-4">
              You have {job.creditBalance} credit{(job.creditBalance || 0) > 1 ? 's' : ''} available.
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => handleDownload('csv')}
                className="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700"
              >
                Use 1 Credit - Download CSV
              </button>
              <button
                onClick={() => handleDownload('qbo')}
                className="bg-purple-600 text-white py-2 px-6 rounded-lg hover:bg-purple-700"
              >
                Use 1 Credit - Download QBO
              </button>
            </div>
          </div>
        )}

        {!isPaid && !hasCredits && job.status === 'pending' && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 mb-4">Ready to process.</p>
            <button
              onClick={handleProcess}
              disabled={processing}
              className="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {processing ? 'Processing...' : 'Start Processing'}
            </button>
          </div>
        )}

        {job.status === 'processing' && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800">Processing your PDF... This may take a moment.</p>
            <button
              onClick={fetchJob}
              className="mt-2 text-blue-600 hover:text-blue-800 underline"
            >
              Refresh Status
            </button>
          </div>
        )}

        {isCompleted && (
          <div className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="font-semibold text-green-800 mb-2">Processing Complete!</h3>
              
              {job.confidenceScore !== undefined && (
                <div className="mb-4">
                  <div className="text-sm text-gray-600 mb-1">Confidence Score</div>
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                      <div
                        className={`h-2 rounded-full ${
                          job.confidenceScore >= 70 ? 'bg-green-500' : 'bg-yellow-500'
                        }`}
                        style={{ width: `${job.confidenceScore}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold">{job.confidenceScore}%</span>
                  </div>
                  {job.confidenceScore < 70 && (
                    <p className="text-sm text-yellow-700 mt-1">
                      This file may need manual review. Don&apos;t pay if unsure.
                    </p>
                  )}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4 text-sm">
                <div>
                  <div className="text-gray-600">Rows Extracted</div>
                  <div className="font-semibold">{job.rowCount || 0}</div>
                </div>
                {job.dateRangeStart && job.dateRangeEnd && (
                  <div>
                    <div className="text-gray-600">Date Range</div>
                    <div className="font-semibold">
                      {new Date(job.dateRangeStart).toLocaleDateString()} - {new Date(job.dateRangeEnd).toLocaleDateString()}
                    </div>
                  </div>
                )}
              </div>

              {job.totalDebit && job.totalCredit && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 mb-4 text-sm">
                  <div>
                    <div className="text-gray-600">Total Debit</div>
                    <div className="font-semibold">${job.totalDebit}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Total Credit</div>
                    <div className="font-semibold">${job.totalCredit}</div>
                  </div>
                  {job.totalBalance && (
                    <div>
                      <div className="text-gray-600">Balance</div>
                      <div className="font-semibold">${job.totalBalance}</div>
                    </div>
                  )}
                </div>
              )}

              {/* Sample CSV rows preview */}
              {job.sampleRows && job.sampleRows.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Sample Output (First {job.sampleRows.length - 1} rows):</h4>
                  <div className="overflow-x-auto border border-gray-200 rounded-lg -mx-2 sm:mx-0">
                    <table className="min-w-full divide-y divide-gray-200 text-xs sm:text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          {job.sampleRows[0]?.map((header, idx) => (
                            <th
                              key={idx}
                              className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {job.sampleRows.slice(1).map((row, rowIdx) => (
                          <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            {row.map((cell, cellIdx) => (
                              <td
                                key={cellIdx}
                                className="px-3 py-2 text-xs text-gray-900 whitespace-nowrap"
                              >
                                {cell || '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Preview shows first {job.sampleRows.length - 1} transaction rows. Click &quot;Preview CSV&quot; to see full file with watermark.
                  </p>
                </div>
              )}

              {/* Download buttons (only if paid or has credits) */}
              {canDownload && (
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
              <button
                onClick={() => handleDownload('csv')}
                className="bg-blue-600 text-white py-2.5 px-6 rounded-lg hover:bg-blue-700 text-sm sm:text-base"
              >
                Download CSV
              </button>
              <button
                onClick={() => handleDownload('qbo')}
                className="bg-purple-600 text-white py-2.5 px-6 rounded-lg hover:bg-purple-700 text-sm sm:text-base"
              >
                Download QBO
              </button>
            </div>
              )}
            </div>
          </div>
        )}

        {isFailed && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 mb-4">Processing failed. Please try uploading again.</p>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Support token:</span>
              <code className="px-2 py-1 bg-gray-100 rounded text-sm font-mono">{jobId}</code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(jobId)
                  alert('Support token copied to clipboard!')
                }}
                className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
              >
                Copy
              </button>
            </div>
          </div>
        )}

        {/* Support token - always visible */}
        <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Support token:</span>
            <code className="px-2 py-1 bg-white rounded text-sm font-mono">{jobId}</code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(jobId)
                alert('Support token copied to clipboard!')
              }}
              className="px-3 py-1 text-sm bg-white hover:bg-gray-100 border border-gray-300 rounded"
            >
              Copy
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}
