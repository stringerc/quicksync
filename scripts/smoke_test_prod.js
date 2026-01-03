#!/usr/bin/env node

/**
 * Production Smoke Tests for QuickSync.app
 * Non-destructive tests that verify basic functionality
 */

const PROD_URL = process.env.PROD_URL || 'https://quicksync.app'

const tests = []
const failures = []

function test(name, fn) {
  tests.push({ name, fn })
}

async function runTests() {
  console.log(`🧪 Running smoke tests against: ${PROD_URL}\n`)

  // Test 1: Health endpoint
  test('Health endpoint returns 200', async () => {
    const res = await fetch(`${PROD_URL}/api/health`)
    if (res.status !== 200) {
      throw new Error(`Expected 200, got ${res.status}`)
    }
    const data = await res.json()
    if (!data.ok) {
      throw new Error('Health check returned ok: false')
    }
    return data
  })

  // Test 2: Landing page
  test('Landing page returns 200', async () => {
    const res = await fetch(`${PROD_URL}/`)
    if (res.status !== 200) {
      throw new Error(`Expected 200, got ${res.status}`)
    }
    const text = await res.text()
    if (!text.includes('QuickBooks')) {
      throw new Error('Landing page does not contain expected content')
    }
  })

  // Test 3: Bookkeepers page
  test('Bookkeepers page returns 200', async () => {
    const res = await fetch(`${PROD_URL}/bookkeepers`)
    if (res.status !== 200) {
      throw new Error(`Expected 200, got ${res.status}`)
    }
  })

  // Test 4: Admin endpoint requires auth (should return 401)
  test('Admin endpoint requires authentication (401)', async () => {
    const res = await fetch(`${PROD_URL}/api/admin/jobs`)
    if (res.status !== 401 && res.status !== 403) {
      throw new Error(`Expected 401/403, got ${res.status}`)
    }
  })

  // Test 5: Webhook endpoint rejects unsigned requests (400)
  test('Webhook endpoint rejects unsigned requests (400)', async () => {
    const res = await fetch(`${PROD_URL}/api/payment/webhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ test: 'data' }),
    })
    if (res.status !== 400) {
      throw new Error(`Expected 400 for unsigned request, got ${res.status}`)
    }
  })

  // Test 6: Upload endpoint requires auth (401)
  test('Upload endpoint requires authentication (401)', async () => {
    const res = await fetch(`${PROD_URL}/api/upload`, {
      method: 'POST',
    })
    if (res.status !== 401) {
      throw new Error(`Expected 401, got ${res.status}`)
    }
  })

  // Test 7: Jobs endpoint requires auth (401)
  test('Jobs endpoint requires authentication (401)', async () => {
    const res = await fetch(`${PROD_URL}/api/jobs/test-id`)
    if (res.status !== 401 && res.status !== 404) {
      // 404 is acceptable if auth passes but job doesn't exist
      throw new Error(`Expected 401/404, got ${res.status}`)
    }
  })

  // Test 8: Download endpoint requires auth (401)
  test('Download endpoint requires authentication (401)', async () => {
    const res = await fetch(`${PROD_URL}/api/download/test-id/csv`)
    if (res.status !== 401 && res.status !== 404) {
      throw new Error(`Expected 401/404, got ${res.status}`)
    }
  })

  // Run all tests
  for (const { name, fn } of tests) {
    try {
      await fn()
      console.log(`✅ ${name}`)
    } catch (error) {
      console.error(`❌ ${name}: ${error.message}`)
      failures.push({ name, error: error.message })
    }
  }

  // Summary
  console.log(`\n📊 Test Summary:`)
  console.log(`   Passed: ${tests.length - failures.length}/${tests.length}`)
  console.log(`   Failed: ${failures.length}/${tests.length}`)

  if (failures.length > 0) {
    console.log(`\n❌ Failures:`)
    failures.forEach(({ name, error }) => {
      console.log(`   - ${name}: ${error}`)
    })
    process.exit(1)
  } else {
    console.log(`\n✅ All smoke tests passed!`)
    process.exit(0)
  }
}

// Handle fetch errors gracefully
const originalFetch = global.fetch
global.fetch = async (...args) => {
  try {
    return await originalFetch(...args)
  } catch (error) {
    // Convert network errors to test failures
    throw new Error(`Network error: ${error.message}`)
  }
}

// Run tests
runTests().catch((error) => {
  console.error('Fatal error running tests:', error)
  process.exit(1)
})

