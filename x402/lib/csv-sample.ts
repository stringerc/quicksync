/**
 * Utility to extract sample rows from CSV content
 */
export function getSampleRowsFromCSV(csvContent: string, maxRows: number = 5): string[][] {
  const lines = csvContent.trim().split('\n').filter(line => line.trim().length > 0)
  if (lines.length === 0) return []

  // Parse CSV (simple parser - handles quoted fields)
  const parseCSVLine = (line: string): string[] => {
    const result: string[] = []
    let current = ''
    let inQuotes = false

    for (let i = 0; i < line.length; i++) {
      const char = line[i]
      const nextChar = line[i + 1]

      if (char === '"') {
        if (inQuotes && nextChar === '"') {
          // Escaped quote
          current += '"'
          i++ // Skip next quote
        } else {
          // Toggle quote state
          inQuotes = !inQuotes
        }
      } else if (char === ',' && !inQuotes) {
        // Field separator
        result.push(current.trim())
        current = ''
      } else {
        current += char
      }
    }
    result.push(current.trim()) // Add last field
    return result
  }

  const rows: string[][] = []
  const rowsToTake = Math.min(lines.length, maxRows + 1) // +1 for header

  for (let i = 0; i < rowsToTake; i++) {
    const parsed = parseCSVLine(lines[i])
    rows.push(parsed)
  }

  return rows
}

