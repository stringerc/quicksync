'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface JobListProps {
  token: string
}

interface Job {
  id: string
  fileName: string
  status: string
  paymentStatus: string
  createdAt: string
  rowCount?: number
  confidenceScore?: number
}

export default function JobList({ token }: JobListProps) {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Note: This is a placeholder - you'd need to create an API endpoint to list jobs
  // For now, jobs are accessed individually via /jobs/[id]
  
  useEffect(() => {
    // In a real implementation, fetch jobs from /api/jobs
    setLoading(false)
  }, [])

  if (loading) {
    return <div className="text-gray-600">Loading jobs...</div>
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Recent Jobs</h2>
      <p className="text-gray-600 text-sm">
        Navigate to a job page using the URL: /jobs/[job-id]
      </p>
    </div>
  )
}

