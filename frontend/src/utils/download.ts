/**
 * Download utilities for file downloads, CSV export, and URL-based downloads.
 *
 * All functions work by creating temporary DOM elements or fetching blobs —
 * no external libraries required.
 */

// ---------------------------------------------------------------------------
// 1. Blob Download
// ---------------------------------------------------------------------------

/**
 * Triggers a file download from a Blob or File object.
 *
 * Creates a temporary `<a>` element, clicks it, and cleans up. This is the
 * lowest-level download primitive.
 *
 * @param blob     - The Blob (or File) to download.
 * @param filename - The suggested filename for the download.
 */
export function downloadFile(blob: Blob, filename: string): void {
  // Create a blob URL
  const url = window.URL.createObjectURL(blob)

  // Create a temporary anchor element
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'

  // Append to body, click, and remove
  document.body.appendChild(link)
  link.click()

  // Cleanup — defer revoke to allow the browser to start the download
  setTimeout(() => {
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }, 150)
}

// ---------------------------------------------------------------------------
// 2. Download from URL
// ---------------------------------------------------------------------------

/**
 * Downloads a file by fetching it from a remote URL as a blob.
 *
 * This is useful when the file is served from a different endpoint and you
 * want to ensure the filename is set client-side, or when downloading files
 * that require auth headers (handled by the axios instance in request.ts).
 *
 * @param url      - The URL to fetch the file from.
 * @param filename - The suggested filename for the downloaded file.
 * @returns A Promise that resolves when the download is initiated.
 */
export async function downloadFromUrl(
  url: string,
  filename: string,
): Promise<void> {
  try {
    const response = await fetch(url, {
      headers: {
        // Include auth token if available
        ...(localStorage.getItem('token')
          ? { Authorization: `Bearer ${localStorage.getItem('token')}` }
          : {}),
      },
    })

    if (!response.ok) {
      throw new Error(`下载失败: HTTP ${response.status}`)
    }

    const blob = await response.blob()
    downloadFile(blob, filename)
  } catch (error) {
    console.error('[downloadFromUrl] Error:', error)
    throw error
  }
}

// ---------------------------------------------------------------------------
// 3. CSV Export
// ---------------------------------------------------------------------------

/**
 * Column definition for CSV export.
 */
export interface CsvColumn {
  /** The key in the data object to extract. */
  key: string
  /** The column header / title. */
  title: string
  /**
   * Optional formatter function for the cell value.
   * Receives the raw value and the full row object.
   * Return the formatted string for the cell.
   */
  formatter?: (value: unknown, row: Record<string, unknown>) => string
}

/**
 * Converts an array of objects to a CSV string.
 *
 * @param data    - Array of data objects.
 * @param columns - Column definitions (key, title, optional formatter).
 * @returns A CSV-formatted string.
 */
function toCsvString(
  data: Record<string, unknown>[],
  columns: CsvColumn[],
): string {
  // Build header row
  const header = columns.map((col) => escapeCsvField(col.title)).join(',')

  // Build data rows
  const rows = data.map((row) =>
    columns
      .map((col) => {
        const rawValue = row[col.key]
        const displayValue = col.formatter
          ? col.formatter(rawValue, row)
          : rawValue != null
            ? String(rawValue)
            : ''
        return escapeCsvField(displayValue)
      })
      .join(','),
  )

  return [header, ...rows].join('\r\n')
}

/**
 * Escapes a field value for safe CSV inclusion.
 *
 * Wraps the value in double quotes if it contains commas, quotes, newlines,
 * or leading/trailing whitespace. Doubles any embedded double quotes.
 */
function escapeCsvField(value: string): string {
  if (
    value.includes(',') ||
    value.includes('"') ||
    value.includes('\n') ||
    value.includes('\r') ||
    value.startsWith(' ') ||
    value.endsWith(' ')
  ) {
    return '"' + value.replace(/"/g, '""') + '"'
  }
  return value
}

/**
 * Converts an array of objects to CSV and triggers a download.
 *
 * Inserts a UTF-8 BOM prefix so that Microsoft Excel correctly detects the
 * encoding for Chinese characters.
 *
 * @param data     - Array of data objects to export.
 * @param filename - The filename (without extension — ".csv" is appended).
 * @param columns  - Column definitions controlling which fields are exported
 *                   and what their headers are.
 *
 * @example
 * ```ts
 * exportToCsv(contracts, '合同列表', [
 *   { key: 'title', title: '合同名称' },
 *   { key: 'partyA', title: '甲方' },
 *   { key: 'amount', title: '金额', formatter: (v) => formatMoney(Number(v)) },
 * ])
 * ```
 */
export function exportToCsv(
  data: Record<string, unknown>[],
  filename: string,
  columns: CsvColumn[],
): void {
  if (!data || data.length === 0) {
    console.warn('[exportToCsv] No data to export.')
    return
  }

  if (!columns || columns.length === 0) {
    console.warn('[exportToCsv] No columns defined.')
    return
  }

  const csvString = toCsvString(data, columns)

  // Prepend BOM for Excel UTF-8 compatibility (critical for Chinese characters)
  const bom = '﻿'
  const blob = new Blob([bom + csvString], {
    type: 'text/csv;charset=utf-8;',
  })

  const fullFilename = filename.endsWith('.csv') ? filename : `${filename}.csv`
  downloadFile(blob, fullFilename)
}

// ---------------------------------------------------------------------------
// 4. JSON Export
// ---------------------------------------------------------------------------

/**
 * Exports data as a formatted JSON file.
 *
 * @param data     - The data to export (will be JSON.stringify'd with indentation).
 * @param filename - The filename (".json" is appended if missing).
 */
export function exportToJson(
  data: unknown,
  filename: string,
): void {
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' })
  const fullFilename = filename.endsWith('.json') ? filename : `${filename}.json`
  downloadFile(blob, fullFilename)
}

// ---------------------------------------------------------------------------
// 5. Excel-Style XLSX (simple HTML table approach)
// ---------------------------------------------------------------------------

/**
 * Exports data as an Excel-compatible HTML table file (.xls).
 *
 * This is a lightweight alternative to full xlsx libraries. Excel will open
 * the HTML file and render it as a spreadsheet. Supports basic formatting.
 *
 * @param data    - Array of data objects.
 * @param filename - The filename (".xls" is appended if missing).
 * @param columns - Column definitions.
 */
export function exportToExcel(
  data: Record<string, unknown>[],
  filename: string,
  columns: CsvColumn[],
): void {
  if (!data || data.length === 0) {
    console.warn('[exportToExcel] No data to export.')
    return
  }

  // Build an HTML table that Excel can parse
  const headerCells = columns
    .map((col) => `<th style="border:1px solid #000;padding:6px 12px;background:#f0f0f0;font-weight:bold;">${escapeHtml(col.title)}</th>`)
    .join('')

  const dataRows = data
    .map(
      (row) =>
        '<tr>' +
        columns
          .map((col) => {
            const raw = row[col.key]
            const display = col.formatter
              ? col.formatter(raw, row)
              : raw != null
                ? String(raw)
                : ''
            return `<td style="border:1px solid #ccc;padding:4px 12px;">${escapeHtml(display)}</td>`
          })
          .join('') +
        '</tr>',
    )
    .join('')

  const html = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office"
          xmlns:x="urn:schemas-microsoft-com:office:excel"
          xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="UTF-8">
        <!--[if gte mso 9]><xml><x:ExcelWorkbook>
          <x:ExcelWorksheets><x:ExcelWorksheet>
            <x:Name>Sheet1</x:Name><x:WorksheetOptions>
              <x:DisplayGridlines/>
            </x:WorksheetOptions>
          </x:ExcelWorksheet></x:ExcelWorksheets>
        </x:ExcelWorkbook></xml><![endif]-->
      </head>
      <body>
        <table style="border-collapse:collapse;">
          <thead><tr>${headerCells}</tr></thead>
          <tbody>${dataRows}</tbody>
        </table>
      </body>
    </html>
  `

  const blob = new Blob(['﻿' + html], {
    type: 'application/vnd.ms-excel;charset=utf-8;',
  })
  const fullFilename = filename.endsWith('.xls') ? filename : `${filename}.xls`
  downloadFile(blob, fullFilename)
}

/**
 * Escapes HTML special characters in a string.
 */
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }
  return text.replace(/[&<>"']/g, (ch) => map[ch] || ch)
}

// ---------------------------------------------------------------------------
// 6. Batch download helper
// ---------------------------------------------------------------------------

/**
 * Downloads multiple files in sequence with a configurable delay between each.
 *
 * @param files   - Array of {url, filename} pairs.
 * @param delayMs - Delay in milliseconds between downloads (default: 500).
 */
export async function downloadBatch(
  files: Array<{ url: string; filename: string }>,
  delayMs: number = 500,
): Promise<void> {
  for (let i = 0; i < files.length; i++) {
    const { url, filename } = files[i]
    try {
      await downloadFromUrl(url, filename)
      if (i < files.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, delayMs))
      }
    } catch (error) {
      console.error(`[downloadBatch] Failed to download "${filename}":`, error)
      throw error
    }
  }
}
