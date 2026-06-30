export type OutputFormat = 'pdf' | 'png'
export type QualityScale = 1 | 2 | 3

export interface AnalyzeResponse {
  filename: string
  label_count: number
  total_quantity: number
  has_quantity_commands: boolean
}

export interface RuntimeInfo {
  available: boolean
  description: string
  detail: string
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  version: string
  runtime: RuntimeInfo
}

export interface ConversionSettings {
  outputFormat: OutputFormat
  widthIn: number
  heightIn: number
  dpmm: number
  qualityScale: QualityScale
  channelsPerRow: number
  dieCutEnabled: boolean
  dieCutMarginMm: number
  dieCutColumns: number
  pngPrefix: string
}

export interface DownloadResult {
  blob: Blob
  filename: string
  generatedFiles: number
  renderedLabels: number
}
