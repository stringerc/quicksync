import pdfParse from 'pdf-parse'
import { parse as parseDate } from 'date-fns'

export interface Transaction {
  date: Date
  description: string
  debit: number | null
  credit: number | null
  balance: number | null
  rawRow: string[]
}

export interface ParseResult {
  transactions: Transaction[]
  confidenceScore: number
  metadata: {
    dateRange: { start: Date | null; end: Date | null }
    totals: { debit: number; credit: number; balance: number | null }
  }
}

/**
 * Extract text from PDF buffer
 */
export async function extractPDFText(pdfBuffer: Buffer): Promise<string> {
  const data = await pdfParse(pdfBuffer)
  return data.text
}

/**
 * Check if a line looks like a non-transaction (header, summary, page number, etc.)
 */
function isNonTransactionLine(line: string): boolean {
  const lowerLine = line.toLowerCase()
  
  // Common non-transaction patterns
  const nonTransactionPatterns = [
    // Headers and section labels
    /^(account summary|beginning balance|ending balance|deposits and other additions|atm and debit card subtractions|other subtractions|checks|service fees|total)/i,
    /^(date\s*description|date\s*transaction|date\s*amount)/i,
    /^(customer service|en español|braille|large print)/i,
    // Summary rows
    /^total\s+/i,
    /^subtotal/i,
    /^summary/i,
    // Page numbers
    /^page\s+\d+\s+of\s+\d+/i,
    /^\d+\s+of\s+\d+$/,
    // Section headers
    /^we refunded/i,
    /^total overdraft fees/i,
    /^total nsf/i,
    // Empty or very short lines that are just labels
    /^[a-z\s]{0,20}$/i,
    // Lines that are just dates or amounts without context
    /^\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}\s*$/,
    /^[\$]?[\d,]+\.\d{2}\s*$/,
  ]
  
  return nonTransactionPatterns.some(pattern => pattern.test(line))
}

/**
 * Parse and validate a date, fixing common year issues
 */
function parseAndValidateDate(dateStr: string, patterns: RegExp[]): Date | null {
  const currentYear = new Date().getFullYear()
  const minYear = 2000
  const maxYear = currentYear + 1 // Allow next year for future transactions
  
  for (const pattern of patterns) {
    const match = dateStr.match(pattern)
    if (match) {
      try {
        let normalizedDateStr = match[1].replace(/[-\/]/g, '-')
        
        // Fix year issues: "0025" -> "2025", "025" -> "2025"
        const yearMatch = normalizedDateStr.match(/(\d{1,2})[-\/](\d{1,2})[-\/](\d{2,4})/)
        if (yearMatch) {
          let year = parseInt(yearMatch[3])
          // Fix 2-digit years: 00-30 -> 2000-2030, 31-99 -> 1931-1999
          if (year < 100) {
            if (year <= 30) {
              year = 2000 + year
            } else {
              year = 1900 + year
            }
          }
          // Fix 3-digit years (e.g., 025 -> 2025)
          if (year < 1000 && year > 0) {
            year = 2000 + (year % 100)
          }
          normalizedDateStr = `${yearMatch[1]}-${yearMatch[2]}-${year}`
        }
        
        // Try parsing with different formats
        let date: Date | null = null
        const formats = [
          ['MM-dd-yyyy', normalizedDateStr],
          ['yyyy-MM-dd', normalizedDateStr],
          ['MMM d, yyyy', match[1]],
        ]
        
        for (const [format, str] of formats) {
          try {
            date = parseDate(str, format as any, new Date())
            if (!isNaN(date.getTime())) {
              // Validate year is in reasonable range
              const year = date.getFullYear()
              if (year >= minYear && year <= maxYear) {
                return date
              }
            }
          } catch {
            continue
          }
        }
      } catch {
        continue
      }
    }
  }
  
  return null
}

/**
 * Check if a line looks like a real transaction
 */
function looksLikeTransaction(line: string, hasDate: boolean, amounts: number[]): boolean {
  // Must have at least a date or amounts
  if (!hasDate && amounts.length === 0) {
    return false
  }
  
  // Filter out non-transaction patterns
  if (isNonTransactionLine(line)) {
    return false
  }
  
  // Real transactions typically have:
  // - A date at the start (MM/DD or MM-DD format)
  // - A description (merchant/vendor name)
  // - At least one amount
  
  // Check for transaction-like patterns
  const transactionPattern = /^\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}/ // Date at start
  const hasTransactionPattern = transactionPattern.test(line)
  
  // Description should have some text (not just numbers/dates)
  const description = line
    .replace(/[\d,]+\.\d{2}/g, '')
    .replace(/[\$]/g, '')
    .replace(/\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}/g, '')
    .trim()
  
  // Description should be meaningful (at least 3 chars, not just punctuation)
  const hasValidDescription = description.length >= 3 && /[a-zA-Z]/.test(description)
  
  // Prefer lines with date at start and valid description
  if (hasTransactionPattern && hasValidDescription && amounts.length > 0) {
    return true
  }
  
  // Also accept lines with date and amounts even if description is shorter
  if (hasDate && amounts.length > 0 && description.length > 0) {
    return true
  }
  
  return false
}

/**
 * Parse transactions from PDF text
 * Improved parser with better filtering and validation
 */
export function parseTransactions(text: string): ParseResult {
  const lines = text.split('\n').map((line) => line.trim()).filter(Boolean)

  const transactions: Transaction[] = []
  let totalDebit = 0
  let totalCredit = 0
  let dates: Date[] = []

  // Common date patterns
  const datePatterns = [
    /(\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4})/,
    /(\d{4}[-\/]\d{1,2}[-\/]\d{1,2})/,
    /([A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4})/,
  ]

  // Common amount patterns
  const amountPattern = /[\$]?([\d,]+\.\d{2})/g

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const nextLine = lines[i + 1] || ''

    // Skip non-transaction lines early
    if (isNonTransactionLine(line)) {
      continue
    }

    // Try to find and validate date
    let date: Date | null = parseAndValidateDate(line, datePatterns)
    if (date) {
      dates.push(date)
    }

    // Extract amounts from line (preserve negative sign)
    const amounts: number[] = []
    // Match amounts including negative sign: -$123.45 or $123.45
    const amountPatternWithSign = /([-]?[\$]?)([\d,]+\.\d{2})/g
    let amountMatch
    while ((amountMatch = amountPatternWithSign.exec(line + ' ' + nextLine)) !== null) {
      const sign = amountMatch[1].includes('-') ? -1 : 1
      const amount = parseFloat(amountMatch[2].replace(/,/g, '')) * sign
      if (!isNaN(amount)) {
        amounts.push(amount)
      }
    }

    // Check if this looks like a real transaction
    if (!looksLikeTransaction(line, !!date, amounts)) {
      continue
    }

    // Clean description: remove dates, amounts, and dollar signs
    let description = line
      .replace(/[\d,]+\.\d{2}/g, '') // Remove amounts
      .replace(/[\$]/g, '') // Remove dollar signs
      .replace(date?.toLocaleDateString() || '', '') // Remove parsed date
      .replace(/\t/g, ' ') // Replace tabs with spaces
      .trim()

    // Remove date patterns from description (e.g., "10/27/25", "10-27-25", "11/03/25")
    description = description.replace(/\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}/g, '').trim()
    // Remove leading/trailing separators and clean up
    description = description.replace(/^[-\s]+|[-\s]+$/g, '').trim()
    // Replace multiple spaces with single space
    description = description.replace(/\s+/g, ' ').trim()

    // Determine debit/credit and balance - SIMPLE: negative = debit, positive = credit
    let debit: number | null = null
    let credit: number | null = null
    let balance: number | null = null

    const prevBalance = transactions.length > 0 ? transactions[transactions.length - 1].balance : null

    if (amounts.length === 1) {
      // Single amount - could be transaction amount or balance
      // If negative, it's a debit; if positive, it's a credit
      if (amounts[0] < 0) {
        debit = Math.abs(amounts[0])
        credit = null
        if (prevBalance !== null) {
          balance = prevBalance - debit
        }
      } else if (amounts[0] > 0) {
        credit = amounts[0]
        debit = null
        if (prevBalance !== null) {
          balance = prevBalance + credit
        }
      } else {
        balance = amounts[0]
      }
    } else if (amounts.length === 2) {
      // Two amounts - typically transaction amount and balance
      const transactionAmount = amounts[0]
      balance = Math.abs(amounts[1]) // Balance is usually positive (take absolute value)
      
      // Transaction amount sign determines debit/credit
      if (transactionAmount < 0) {
        debit = Math.abs(transactionAmount)
        credit = null
      } else if (transactionAmount > 0) {
        credit = transactionAmount
        debit = null
      }
    } else if (amounts.length >= 3) {
      // Multiple amounts - find transaction amount and balance
      // Last amount is typically balance
      balance = Math.abs(amounts[amounts.length - 1])
      
      // Find the transaction amount (usually one of the first amounts)
      // Look for negative amounts (debits) or positive amounts (credits)
      const negativeAmounts = amounts.filter(amt => amt < 0)
      const positiveAmounts = amounts.filter(amt => amt > 0 && amt !== balance)
      
      if (negativeAmounts.length > 0) {
        // Has negative amount = debit
        debit = Math.abs(negativeAmounts[0])
        credit = null
      } else if (positiveAmounts.length > 0) {
        // Has positive amount = credit
        credit = positiveAmounts[0]
        debit = null
      }
    }

    // If no date, use previous transaction date (don't use current date as fallback)
    if (!date && transactions.length > 0) {
      date = transactions[transactions.length - 1].date
    } else if (!date) {
      // Skip if no date and no previous transactions
      continue
    }

    // Final validation: description must be meaningful
    if (description.length >= 3 && /[a-zA-Z0-9]/.test(description)) {
      // If balance is missing, calculate from previous transaction
      if (balance === null && transactions.length > 0) {
        const prevBalanceValue = transactions[transactions.length - 1].balance
        if (prevBalanceValue !== null) {
          if (credit !== null) {
            balance = prevBalanceValue + credit
          } else if (debit !== null) {
            balance = prevBalanceValue - debit
          }
        }
      }

      transactions.push({
        date,
        description,
        debit: debit || null,
        credit: credit || null,
        balance: balance || null,
        rawRow: [line, nextLine].filter(Boolean),
      })

      if (debit) totalDebit += debit
      if (credit) totalCredit += credit
    }
  }

  // Validation: Remove duplicate transactions
  const uniqueTransactions: Transaction[] = []
  const seenKeys = new Set<string>()
  
  for (const txn of transactions) {
    // Create a unique key: date + description + amount
    const key = `${txn.date.toISOString().split('T')[0]}-${txn.description.substring(0, 50)}-${txn.debit || 0}-${txn.credit || 0}`
    if (!seenKeys.has(key)) {
      seenKeys.add(key)
      uniqueTransactions.push(txn)
    }
  }

  // Validation: Balance calculation verification
  // Check if calculated balances match expected patterns
  let balanceIssues = 0
  for (let i = 1; i < uniqueTransactions.length; i++) {
    const prev = uniqueTransactions[i - 1]
    const curr = uniqueTransactions[i]
    
    if (prev.balance !== null && curr.balance !== null) {
      // Calculate expected balance
      let expectedBalance = prev.balance
      if (curr.credit !== null) {
        expectedBalance += curr.credit
      }
      if (curr.debit !== null) {
        expectedBalance -= curr.debit
      }
      
      // Allow small rounding differences (0.01)
      const diff = Math.abs(expectedBalance - curr.balance)
      if (diff > 0.01) {
        balanceIssues++
      }
    }
  }

  // Validation: Date monotonicity check
  // Dates should be roughly sequential (allow some flexibility for statement formats)
  let dateIssues = 0
  for (let i = 1; i < uniqueTransactions.length; i++) {
    const prev = uniqueTransactions[i - 1].date
    const curr = uniqueTransactions[i].date
    const daysDiff = (curr.getTime() - prev.getTime()) / (1000 * 60 * 60 * 24)
    
    // Flag if date goes backwards significantly (more than 7 days back)
    // or forward too far (more than 365 days forward)
    if (daysDiff < -7 || daysDiff > 365) {
      dateIssues++
    }
  }

  // Calculate confidence score (enhanced with validation)
  const hasDates = dates.length > 0
  const hasTransactions = uniqueTransactions.length > 0
  const avgTransactionLength = uniqueTransactions.length > 0
    ? uniqueTransactions.reduce((sum, t) => sum + t.description.length, 0) / uniqueTransactions.length
    : 0

  let confidenceScore = 0
  if (hasDates) confidenceScore += 30
  if (hasTransactions) confidenceScore += 30
  if (uniqueTransactions.length >= 5) confidenceScore += 20
  if (avgTransactionLength > 10) confidenceScore += 20

  // Reduce confidence for validation issues
  const duplicateCount = transactions.length - uniqueTransactions.length
  if (duplicateCount > uniqueTransactions.length * 0.1) {
    confidenceScore -= 10 // More than 10% duplicates
  }
  if (balanceIssues > uniqueTransactions.length * 0.2) {
    confidenceScore -= 15 // More than 20% balance issues
  }
  if (dateIssues > uniqueTransactions.length * 0.1) {
    confidenceScore -= 10 // More than 10% date issues
  }

  // Date range
  const sortedDates = dates.sort((a, b) => a.getTime() - b.getTime())
  const dateRange = {
    start: sortedDates[0] || null,
    end: sortedDates[sortedDates.length - 1] || null,
  }

  // Recalculate totals from unique transactions
  const finalTotalDebit = uniqueTransactions.reduce((sum, t) => sum + (t.debit || 0), 0)
  const finalTotalCredit = uniqueTransactions.reduce((sum, t) => sum + (t.credit || 0), 0)

  return {
    transactions: uniqueTransactions, // Return deduplicated transactions
    confidenceScore: Math.max(0, Math.min(confidenceScore, 100)), // Ensure 0-100 range
    metadata: {
      dateRange,
      totals: {
        debit: finalTotalDebit,
        credit: finalTotalCredit,
        balance: uniqueTransactions[uniqueTransactions.length - 1]?.balance || null,
      },
    },
  }
}

/**
 * Main parsing function
 */
export async function parsePDF(pdfBuffer: Buffer): Promise<ParseResult> {
  const text = await extractPDFText(pdfBuffer)
  return parseTransactions(text)
}

