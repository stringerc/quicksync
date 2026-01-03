'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { analytics } from '@/lib/analytics'

interface UploadFormProps {
  token?: string | null // Token is now optional - allows anonymous uploads
}

export default function UploadForm({ token }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const router = useRouter()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    analytics.uploadStarted()

    try {
      const formData = new FormData()
      formData.append('file', file)

      // Build headers - only include auth if token exists
      const headers: HeadersInit = {}
      if (token) {
        headers.Authorization = `Bearer ${token}`
      }

      const response = await fetch('/api/upload', {
        method: 'POST',
        headers,
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        const jobId = data.jobId
        const sessionId = data.sessionId // For anonymous jobs
        analytics.uploadCompleted(jobId)
        
        // Store sessionId if it's an anonymous job
        if (sessionId) {
          localStorage.setItem(`job_${jobId}_session`, sessionId)
        }
        
        router.push(`/jobs/${jobId}`)
        
        // Auto-trigger processing after upload (preview before payment)
        try {
          const processHeaders: HeadersInit = {
            'Content-Type': 'application/json',
          }
          if (token) {
            processHeaders.Authorization = `Bearer ${token}`
          }
          
          const processResponse = await fetch('/api/process', {
            method: 'POST',
            headers: processHeaders,
            body: JSON.stringify({ jobId, sessionId }),
          })
          // Don't wait for completion - let user see status on job page
        } catch (err) {
          // Silent fail - processing will happen when user views job page
        }
      } else {
        alert('Upload failed: ' + data.error)
        setUploading(false)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed')
      setUploading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 mb-6 sm:mb-8">
      <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 text-gray-800">Upload PDF</h2>
      
      <div className="space-y-4">
        <div>
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        {file && (
          <div className="text-sm text-gray-600">
            Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
        >
          {uploading ? 'Uploading...' : 'Upload & Process'}
        </button>
      </div>
    </div>
  )
}

