import type {
  AnalyzeResponse,
  ConversionSettings,
  DownloadResult,
  HealthResponse,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    return body.detail ?? `La solicitud fallo con estado ${response.status}.`
  } catch {
    return `La solicitud fallo con estado ${response.status}.`
  }
}

function filenameFromHeader(header: string | null, fallback: string): string {
  if (!header) return fallback
  const utf8Match = header.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match) return decodeURIComponent(utf8Match[1])
  const plainMatch = header.match(/filename="?([^";]+)"?/i)
  return plainMatch?.[1] ?? fallback
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, { signal })
  if (!response.ok) throw new Error(await getErrorMessage(response))
  return response.json() as Promise<HealthResponse>
}

export async function analyzeZpl(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`${API_BASE_URL}/zpl/analyze`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) throw new Error(await getErrorMessage(response))
  return response.json() as Promise<AnalyzeResponse>
}

export async function convertZpl(
  file: File,
  settings: ConversionSettings,
): Promise<DownloadResult> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('output_format', settings.outputFormat)
  formData.append('width_in', String(settings.widthIn))
  formData.append('height_in', String(settings.heightIn))
  formData.append('dpmm', String(settings.dpmm))
  formData.append('quality_scale', String(settings.qualityScale))
  formData.append('channels_per_row', String(settings.channelsPerRow))
  formData.append('die_cut_enabled', String(settings.dieCutEnabled))
  formData.append('die_cut_margin_mm', String(settings.dieCutMarginMm))
  formData.append('die_cut_columns', String(settings.dieCutColumns))
  formData.append('png_prefix', settings.pngPrefix)

  const response = await fetch(`${API_BASE_URL}/zpl/convert`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) throw new Error(await getErrorMessage(response))

  const fallback = settings.outputFormat === 'pdf' ? 'etiquetas.pdf' : 'etiquetas_png.zip'
  return {
    blob: await response.blob(),
    filename: filenameFromHeader(response.headers.get('Content-Disposition'), fallback),
    generatedFiles: Number(response.headers.get('X-Generated-Files') ?? 0),
    renderedLabels: Number(response.headers.get('X-Rendered-Labels') ?? 0),
  }
}

export function downloadBlob(result: DownloadResult): void {
  const url = URL.createObjectURL(result.blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = result.filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
