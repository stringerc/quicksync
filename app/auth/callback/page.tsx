'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

function AuthCallbackContent() {
  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    const token = searchParams.get('token')
    
    if (token) {
      // Token is handled by the API route which sets the cookie
      // Just redirect to home
      router.push('/')
    } else {
      router.push('/')
    }
  }, [searchParams, router])

  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p>Completing sign-in...</p>
      </div>
    </main>
  )
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p>Loading...</p>
        </div>
      </main>
    }>
      <AuthCallbackContent />
    </Suspense>
  )
}

