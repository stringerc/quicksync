import { Transaction } from './pdf-parser'
import { promises as fs } from 'fs'
import path from 'path'
import { format } from 'date-fns'
import { saveFile } from './storage'

/**
 * Generate QBO (QuickBooks) file from transactions
 * QBO is essentially a CSV with specific format and headers
 * Returns the storage path (S3 key or local path)
 */
export async function generateQBO(
  transactions: Transaction[],
  outputPath: string // Can be relative path or S3 key prefix
): Promise<string> {
  const STORAGE_TYPE = process.env.STORAGE_TYPE || 'local'

  const lines: string[] = []

  // QBO Header
  lines.push('!TRNS\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO')
  lines.push('!SPL\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO')
  lines.push('!ENDTRNS')

  // Transactions
  for (const txn of transactions) {
    const date = format(txn.date, 'MM/dd/yyyy')
    const amount = (txn.debit ? -txn.debit : txn.credit) || 0
    const account = txn.debit ? 'Expenses' : 'Income'
    const memo = txn.description

    // Main transaction line
    lines.push(`TRNS\t\t${date}\t${account}\t\t${amount.toFixed(2)}\t${memo}`)
    // Split line (for double-entry accounting)
    lines.push(`SPL\t\t${date}\tBank Account\t\t${(-amount).toFixed(2)}\t${memo}`)
    lines.push('ENDTRNS')
  }

  const qboContent = lines.join('\n')
  const qboBuffer = Buffer.from(qboContent, 'utf-8')

  if (STORAGE_TYPE === 's3') {
    // For S3, use the outputPath as the key prefix
    const key = outputPath.endsWith('.qbo') ? outputPath : `${outputPath}.qbo`
    const result = await saveFile(qboBuffer, 'output.qbo', path.dirname(key))
    return result.filePath
  } else {
    // For local storage, write directly to filesystem
    await fs.mkdir(path.dirname(outputPath), { recursive: true })
    await fs.writeFile(outputPath, qboBuffer)
    return outputPath
  }
}

