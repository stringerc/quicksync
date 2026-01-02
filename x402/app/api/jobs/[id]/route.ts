import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { getCurrentUser } from '@/lib/auth'
import { getCreditBalance } from '@/lib/credits'
import { readFile } from '@/lib/storage'
import { getSampleRowsFromCSV } from '@/lib/csv-sample'

export const dynamic = 'force-dynamic'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const authHeader = request.headers.get('authorization')
    const user = await getCurrentUser(authHeader) // Optional - can be null for anonymous jobs

    const job = await prisma.job.findUnique({
      where: { id: params.id },
    })

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    // Allow access if:
    // 1. User is authenticated and owns the job
    // 2. Job is anonymous (no userId) - anyone can view
    // 3. Job has userId but no user is logged in - allow viewing (they'll need to pay/auth to download)
    if (job.userId && user && job.userId !== user.id) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }

    // Get credit balance if user is logged in
    const creditBalance = user ? await getCreditBalance(user.id) : 0

    // Get sample rows from CSV if available
    let sampleRows: string[][] = []
    if (job.csvFilePath && job.status === 'completed') {
      try {
        const csvBuffer = await readFile(job.csvFilePath)
        const csvContent = csvBuffer.toString('utf-8')
        sampleRows = getSampleRowsFromCSV(csvContent, 5) // Get first 5 rows (including header)
      } catch (error) {
        // If we can't read the CSV, just continue without sample rows
        console.error('Failed to read CSV for sample rows:', error)
      }
    }

    return NextResponse.json({
      id: job.id,
      fileName: job.fileName,
      status: job.status,
      paymentStatus: job.paymentStatus,
      createdAt: job.createdAt.toISOString(),
      processedAt: job.processedAt?.toISOString(),
      paidAt: job.paidAt?.toISOString(),
      creditRedeemedAt: job.creditRedeemedAt?.toISOString(),
      reviewRequestedAt: job.reviewRequestedAt?.toISOString(),
      rowCount: job.rowCount,
      dateRangeStart: job.dateRangeStart?.toISOString(),
      dateRangeEnd: job.dateRangeEnd?.toISOString(),
      totalDebit: job.totalDebit,
      totalCredit: job.totalCredit,
      totalBalance: job.totalBalance,
      confidenceScore: job.confidenceScore,
      csvFilePath: job.csvFilePath,
      qboFilePath: job.qboFilePath,
      previewCsvFilePath: job.previewCsvFilePath, // Add preview paths
      previewQboFilePath: job.previewQboFilePath,
      creditBalance,
      sampleRows, // Add sample rows
    })
  } catch (error) {
    console.error('Get job error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch job' },
      { status: 500 }
    )
  }
}

