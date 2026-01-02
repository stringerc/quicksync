import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { readFile, saveFile } from '@/lib/storage'
import { parsePDF } from '@/lib/pdf-parser'
import { generateCSV } from '@/lib/csv-generator'
import { generateQBO } from '@/lib/qbo-generator'
import { addWatermarkToPDF, addWatermarkToCSV } from '@/lib/watermark'
import path from 'path'
import { promises as fs } from 'fs'
import { getCurrentUser } from '@/lib/auth'
import { logger } from '@/lib/logger'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

export async function POST(request: NextRequest) {
  let user: any = null
  
  try {
    // Authentication is optional - support anonymous jobs via sessionId
    const authHeader = request.headers.get('authorization')
    user = await getCurrentUser(authHeader)

    const body = await request.json()
    const { jobId, sessionId } = body

    if (!jobId) {
      return NextResponse.json({ error: 'Job ID required' }, { status: 400 })
    }

    // Get job
    const job = await prisma.job.findUnique({
      where: { id: jobId },
    })

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    // Verify access: user must match OR sessionId must match (for anonymous jobs)
    if (job.userId && job.userId !== user?.id) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    
    if (!job.userId && job.sessionId !== sessionId) {
      return NextResponse.json({ error: 'Invalid session' }, { status: 403 })
    }

    // Payment is NOT required for processing - users can preview results before paying

    // Update status to processing
    await prisma.job.update({
      where: { id: jobId },
      data: { status: 'processing' },
    })

    logger.info('Processing started', { 
      jobId, 
      userId: user?.id || 'anonymous', 
      sessionId: job.sessionId || null,
      fileName: job.fileName 
    })

    try {
      // Read PDF file
      const pdfBuffer = await readFile(job.filePath)

      // Parse PDF
      const parseResult = await parsePDF(pdfBuffer)

      // Generate output files
      // For local storage, use filesystem paths
      // For S3, use key prefixes (the generators will handle the actual storage)
      const STORAGE_TYPE = process.env.STORAGE_TYPE || 'local'
      
      let csvPath: string
      let qboPath: string
      
      if (STORAGE_TYPE === 's3') {
        // For S3, use key prefixes
        csvPath = `outputs/${jobId}/output.csv`
        qboPath = `outputs/${jobId}/output.qbo`
      } else {
        // For local storage, use filesystem paths
        const outputDir = path.join(
          process.env.STORAGE_PATH || './storage',
          'outputs',
          jobId
        )
        csvPath = path.join(outputDir, 'output.csv')
        qboPath = path.join(outputDir, 'output.qbo')
      }

      const finalCsvPath = await generateCSV(parseResult.transactions, csvPath)
      const finalQboPath = await generateQBO(parseResult.transactions, qboPath)

      // Generate watermarked preview files
      let previewCsvPath: string | null = null
      let previewQboPath: string | null = null

      try {
        // Read the generated CSV and create watermarked HTML preview
        const csvContent = await readFile(finalCsvPath)
        const csvString = csvContent.toString('utf-8')
        const watermarkedHtml = addWatermarkToCSV(csvString)
        const htmlBuffer = Buffer.from(watermarkedHtml, 'utf-8')

        // Save watermarked preview
        const previewCsvStoragePath = STORAGE_TYPE === 's3' 
          ? `outputs/${jobId}/preview.csv.html`
          : path.join(path.dirname(csvPath), 'preview.csv.html')
        
        if (STORAGE_TYPE === 's3') {
          const result = await saveFile(htmlBuffer, 'preview.csv.html', `outputs/${jobId}`)
          previewCsvPath = result.filePath
        } else {
          await fs.mkdir(path.dirname(previewCsvStoragePath), { recursive: true })
          await fs.writeFile(previewCsvStoragePath, htmlBuffer)
          previewCsvPath = previewCsvStoragePath
        }

        // For QBO, create watermarked PDF preview from the original PDF
        // (QBO is text-based, so we'll create a simple text preview with watermark)
        const originalPdfBuffer = await readFile(job.filePath)
        const watermarkedPdfBuffer = await addWatermarkToPDF(originalPdfBuffer)
        
        const previewQboStoragePath = STORAGE_TYPE === 's3'
          ? `outputs/${jobId}/preview.qbo.pdf`
          : path.join(path.dirname(qboPath), 'preview.qbo.pdf')
        
        if (STORAGE_TYPE === 's3') {
          const result = await saveFile(watermarkedPdfBuffer, 'preview.qbo.pdf', `outputs/${jobId}`)
          previewQboPath = result.filePath
        } else {
          await fs.mkdir(path.dirname(previewQboStoragePath), { recursive: true })
          await fs.writeFile(previewQboStoragePath, watermarkedPdfBuffer)
          previewQboPath = previewQboStoragePath
        }
      } catch (watermarkError) {
        logger.error('Watermark generation failed', {
          jobId,
          error: String(watermarkError),
        })
        // Continue even if watermarking fails - previews are optional
      }

      // Determine status based on confidence
      const status = parseResult.confidenceScore >= 70 ? 'completed' : 'needs_review'

      // Update job with results
      await prisma.job.update({
        where: { id: jobId },
        data: {
          status,
          processedAt: new Date(),
          rowCount: parseResult.transactions.length,
          dateRangeStart: parseResult.metadata.dateRange.start,
          dateRangeEnd: parseResult.metadata.dateRange.end,
          totalDebit: parseResult.metadata.totals.debit.toFixed(2),
          totalCredit: parseResult.metadata.totals.credit.toFixed(2),
          totalBalance: parseResult.metadata.totals.balance?.toFixed(2) || null,
          confidenceScore: parseResult.confidenceScore,
          csvFilePath: finalCsvPath,
          qboFilePath: finalQboPath,
          previewCsvFilePath: previewCsvPath,
          previewQboFilePath: previewQboPath,
        },
      })

      logger.info('Processing completed', {
        jobId,
        status,
        rowCount: parseResult.transactions.length,
        confidenceScore: parseResult.confidenceScore,
      })

      return NextResponse.json({
        success: true,
        status,
        rowCount: parseResult.transactions.length,
        confidenceScore: parseResult.confidenceScore,
      })
    } catch (error) {
      logger.error('Processing error', {
        jobId,
        error: String(error),
        userId: user?.id || 'anonymous',
      })
      await prisma.job.update({
        where: { id: jobId },
        data: { status: 'failed' },
      })

      return NextResponse.json(
        { error: 'Processing failed', details: String(error) },
        { status: 500 }
      )
    }
  } catch (error) {
    logger.error('Process route error', {
      error: String(error),
      userId: user?.id,
    })
    return NextResponse.json(
      { error: 'Failed to process job' },
      { status: 500 }
    )
  }
}

