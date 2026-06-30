import type { AnalyzeResponse, ConversionSettings } from '../types/api'

interface StatsGridProps {
  analysis: AnalyzeResponse | null
  settings: ConversionSettings
}

export function StatsGrid({ analysis, settings }: StatsGridProps) {
  const dpi = settings.dpmm * settings.qualityScale * 25.4
  const columns = settings.dieCutEnabled
    ? settings.dieCutColumns
    : settings.channelsPerRow

  return (
    <div className="stats-grid">
      <article className="stat">
        <span>Etiquetas</span>
        <strong>{analysis?.label_count ?? '—'}</strong>
        <small>ZPL detectadas</small>
      </article>
      <article className="stat">
        <span>Copias</span>
        <strong>{analysis?.total_quantity ?? '—'}</strong>
        <small>{analysis?.has_quantity_commands ? 'Incluye ^PQ' : 'Sin cantidades ^PQ'}</small>
      </article>
      <article className="stat">
        <span>Calidad</span>
        <strong>{dpi.toFixed(0)} DPI</strong>
        <small>{settings.dpmm * settings.qualityScale} dpmm efectivos</small>
      </article>
      <article className="stat">
        <span>Salida</span>
        <strong>{settings.outputFormat.toUpperCase()}</strong>
        <small>{columns} columna(s) por fila</small>
      </article>
    </div>
  )
}
