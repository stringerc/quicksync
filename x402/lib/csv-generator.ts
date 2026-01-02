import { Transaction } from './pdf-parser'
import { promises as fs } from 'fs'
import path from 'path'
import { saveFile } from './storage'

/**
 * Generate CSV file from transactions
 * Returns the storage path (S3 key or local path)
 */
export async function generateCSV(
  transactions: Transaction[],
  outputPath: string // Can be relative path or S3 key prefix
): Promise<string> {
  const STORAGE_TYPE = process.env.STORAGE_TYPE || 'local'

  const records = transactions.map((t) => ({
    date: t.date.toISOString().split('T')[0], // YYYY-MM-DD
    description: t.description,
    debit: t.debit?.toFixed(2) || '',
    credit: t.credit?.toFixed(2) || '',
    balance: t.balance?.toFixed(2) || '',
  }))

  // Convert records to CSV string
  const headers = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
  const csvRows = [
    headers.join(','),
    ...records.map((r) =>
      [
        r.date,
        `"${r.description.replace(/"/g, '""')}"`, // Escape quotes
        r.debit,
        r.credit,
        r.balance,
      ].join(',')
    ),
  ]
  const csvContent = csvRows.join('\n')
  const csvBuffer = Buffer.from(csvContent, 'utf-8')

  if (STORAGE_TYPE === 's3') {
    // For S3, use the outputPath as the key prefix
    const key = outputPath.endsWith('.csv') ? outputPath : `${outputPath}.csv`
    const result = await saveFile(csvBuffer, 'output.csv', path.dirname(key))
    return result.filePath
  } else {
    // For local storage, write directly to filesystem
    await fs.mkdir(path.dirname(outputPath), { recursive: true })
    await fs.writeFile(outputPath, csvBuffer)
    return outputPath
  }
}

