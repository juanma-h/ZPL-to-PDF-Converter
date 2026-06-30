import type { ConversionSettings } from '../types/api'

interface MaterialPreviewProps {
  settings: ConversionSettings
}

export function MaterialPreview({ settings }: MaterialPreviewProps) {
  const columns = settings.dieCutEnabled ? settings.dieCutColumns : settings.channelsPerRow
  const aspectRatio = settings.widthIn / settings.heightIn

  return (
    <section className="preview" aria-label="Vista previa de composicion">
      <div className="preview__header">
        <div>
          <span className="eyebrow">Vista previa</span>
          <h3>{settings.dieCutEnabled ? 'Material troquelado' : 'Composicion continua'}</h3>
        </div>
        <span className="pill">{columns} columna(s)</span>
      </div>
      <div
        className="preview__canvas"
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(36px, 1fr))` }}
      >
        {Array.from({ length: columns }, (_, index) => (
          <div
            className="preview__cell"
            key={index}
            style={{ padding: settings.dieCutEnabled ? `${Math.min(settings.dieCutMarginMm, 12)}px` : 0 }}
          >
            <div className="preview__label" style={{ aspectRatio }}>
              <span>ZPL</span>
              <i />
              <i />
              <i />
            </div>
          </div>
        ))}
      </div>
      <p>
        Area util: {(settings.widthIn * 25.4).toFixed(1)} ×{' '}
        {(settings.heightIn * 25.4).toFixed(1)} mm
        {settings.dieCutEnabled && ` · margen ${settings.dieCutMarginMm.toFixed(1)} mm`}
      </p>
    </section>
  )
}
