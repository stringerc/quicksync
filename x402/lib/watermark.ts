import { PDFDocument, rgb, PDFFont, PDFPage } from 'pdf-lib'
import fs from 'fs/promises'

/**
 * Adds a diagonal watermark to a PDF buffer
 * @param pdfBuffer - The PDF file buffer
 * @param watermarkText - Text to display in watermark (default: "PREVIEW - quicksync.app")
 * @param opacity - Opacity of watermark (0.0 to 1.0, default: 0.3)
 * @returns Buffer with watermarked PDF
 */
export async function addWatermarkToPDF(
  pdfBuffer: Buffer,
  watermarkText: string = 'PREVIEW - quicksync.app',
  opacity: number = 0.3
): Promise<Buffer> {
  try {
    // Load the PDF
    const pdfDoc = await PDFDocument.load(pdfBuffer)
    const pages = pdfDoc.getPages()

    // Embed a font (using standard fonts)
    // For custom fonts, you'd need to embed them
    const font = await pdfDoc.embedFont('Helvetica-Bold')

    // Add watermark to each page
    for (const page of pages) {
      const { width, height } = page.getSize()

      // Calculate diagonal position (centered)
      const fontSize = Math.min(width, height) * 0.08 // Scale font with page size
      const textWidth = font.widthOfTextAtSize(watermarkText, fontSize)
      const textHeight = fontSize

      // Position text diagonally from bottom-left to top-right
      const angle = -45 * (Math.PI / 180) // -45 degrees in radians
      const centerX = width / 2
      const centerY = height / 2

      // Draw watermark text
      page.drawText(watermarkText, {
        x: centerX - textWidth / 2,
        y: centerY - textHeight / 2,
        size: fontSize,
        font: font,
        color: rgb(0.7, 0.7, 0.7), // Gray color
        opacity: opacity,
        rotate: { angleInRadians: angle },
      })

      // Add additional watermark layer for better coverage (optional)
      // Repeat watermark pattern across the page
      const repeatCount = 3
      for (let i = 0; i < repeatCount; i++) {
        const offsetY = (height / (repeatCount + 1)) * (i + 1) - centerY
        page.drawText(watermarkText, {
          x: centerX - textWidth / 2,
          y: centerY + offsetY - textHeight / 2,
          size: fontSize * 0.8,
          font: font,
          color: rgb(0.7, 0.7, 0.7),
          opacity: opacity * 0.7, // Slightly lighter for repeated watermarks
          rotate: { angleInRadians: angle },
        })
      }
    }

    // Save and return as buffer
    const watermarkedPdfBytes = await pdfDoc.save()
    return Buffer.from(watermarkedPdfBytes)
  } catch (error) {
    console.error('Error adding watermark to PDF:', error)
    throw new Error(`Failed to add watermark: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * Adds watermark text to CSV content (returns HTML with watermark overlay)
 * This creates a preview-friendly version with watermark overlay
 * @param csvContent - The CSV content as string
 * @param watermarkText - Text to display in watermark
 * @returns HTML string with CSV table and watermark overlay
 */
export function addWatermarkToCSV(csvContent: string, watermarkText: string = 'PREVIEW - quicksync.app'): string {
  // Parse CSV into rows
  const lines = csvContent.trim().split('\n')
  if (lines.length === 0) return ''

  const headers = lines[0].split(',')
  const rows = lines.slice(1).map(line => line.split(','))

  // Generate HTML table with watermark overlay
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      padding: 20px;
      background: white;
      position: relative;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px 12px;
      text-align: left;
    }
    th {
      background-color: #f2f2f2;
      font-weight: bold;
    }
    tr:nth-child(even) {
      background-color: #f9f9f9;
    }
    .watermark {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .watermark-text {
      font-size: 72px;
      font-weight: bold;
      color: rgba(150, 150, 150, 0.3);
      transform: rotate(-45deg);
      white-space: nowrap;
      user-select: none;
    }
  </style>
</head>
<body>
  <table>
    <thead>
      <tr>
        ${headers.map(h => `<th>${escapeHtml(h.trim())}</th>`).join('')}
      </tr>
    </thead>
    <tbody>
      ${rows.map(row => `
        <tr>
          ${row.map(cell => `<td>${escapeHtml(cell.trim())}</td>`).join('')}
        </tr>
      `).join('')}
    </tbody>
  </table>
  <div class="watermark">
    <div class="watermark-text">${escapeHtml(watermarkText)}</div>
  </div>
</body>
</html>
  `

  return html.trim()
}

/**
 * Helper function to escape HTML entities
 */
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }
  return text.replace(/[&<>"']/g, m => map[m])
}

