import type { ConversionSettings, OutputFormat, QualityScale } from '../types/api'

interface SettingsPanelProps {
  settings: ConversionSettings
  disabled?: boolean
  onChange: (settings: ConversionSettings) => void
}

const presets = {
  shipping: { width: 4, height: 6 },
  compact: { width: 4, height: 3 },
  small: { width: 2, height: 1 },
  square: { width: 1, height: 1 },
}

export function SettingsPanel({ settings, disabled, onChange }: SettingsPanelProps) {
  function update<Key extends keyof ConversionSettings>(
    key: Key,
    value: ConversionSettings[Key],
  ): void {
    onChange({ ...settings, [key]: value })
  }

  return (
    <div className="settings">
      <div className="field-group field-group--formats">
        <span className="field-label">Formato de salida</span>
        <div className="segmented">
          {(['pdf', 'png'] as OutputFormat[]).map((format) => (
            <button
              type="button"
              key={format}
              className={settings.outputFormat === format ? 'is-active' : ''}
              onClick={() => update('outputFormat', format)}
              disabled={disabled}
            >
              {format.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <label className="field field--wide">
        <span>Formato de etiqueta</span>
        <select
          defaultValue="shipping"
          disabled={disabled}
          onChange={(event) => {
            const preset = presets[event.target.value as keyof typeof presets]
            if (preset) onChange({ ...settings, widthIn: preset.width, heightIn: preset.height })
          }}
        >
          <option value="shipping">4 × 6 in — Envios</option>
          <option value="compact">4 × 3 in</option>
          <option value="small">2 × 1 in</option>
          <option value="square">1 × 1 in</option>
        </select>
      </label>

      <label className="field">
        <span>Ancho util (in)</span>
        <input
          type="number"
          min="0.5"
          max="20"
          step="0.1"
          value={settings.widthIn}
          disabled={disabled}
          onChange={(event) => update('widthIn', Number(event.target.value))}
        />
      </label>
      <label className="field">
        <span>Alto util (in)</span>
        <input
          type="number"
          min="0.5"
          max="20"
          step="0.1"
          value={settings.heightIn}
          disabled={disabled}
          onChange={(event) => update('heightIn', Number(event.target.value))}
        />
      </label>
      <label className="field">
        <span>Resolucion</span>
        <select
          value={settings.dpmm}
          disabled={disabled}
          onChange={(event) => update('dpmm', Number(event.target.value))}
        >
          <option value="8">8 dpmm — 203 DPI</option>
          <option value="12">12 dpmm — 300 DPI</option>
          <option value="24">24 dpmm — 600 DPI</option>
        </select>
      </label>
      <label className="field">
        <span>Escala de calidad</span>
        <select
          value={settings.qualityScale}
          disabled={disabled}
          onChange={(event) => update('qualityScale', Number(event.target.value) as QualityScale)}
        >
          <option value="1">Normal (1×)</option>
          <option value="2">Alta (2×)</option>
          <option value="3">Ultra (3×)</option>
        </select>
      </label>

      <label className="switch field--wide">
        <input
          type="checkbox"
          checked={settings.dieCutEnabled}
          disabled={disabled}
          onChange={(event) => update('dieCutEnabled', event.target.checked)}
        />
        <span className="switch__control" />
        <span>
          <strong>Material troquelado</strong>
          <small>Agrega margen fisico alrededor de cada etiqueta.</small>
        </span>
      </label>

      {settings.dieCutEnabled ? (
        <>
          <label className="field">
            <span>Margen por lado (mm)</span>
            <input
              type="number"
              min="0"
              max="25"
              step="0.5"
              value={settings.dieCutMarginMm}
              disabled={disabled}
              onChange={(event) => update('dieCutMarginMm', Number(event.target.value))}
            />
          </label>
          <label className="field">
            <span>Columnas del rollo</span>
            <input
              type="number"
              min="1"
              max="6"
              value={settings.dieCutColumns}
              disabled={disabled}
              onChange={(event) => update('dieCutColumns', Number(event.target.value))}
            />
          </label>
        </>
      ) : (
        <label className="field field--wide">
          <span>Canales por fila</span>
          <input
            type="number"
            min="1"
            max="6"
            value={settings.channelsPerRow}
            disabled={disabled}
            onChange={(event) => update('channelsPerRow', Number(event.target.value))}
          />
        </label>
      )}

      {settings.outputFormat === 'png' && (
        <label className="field field--wide">
          <span>Prefijo de archivos PNG</span>
          <input
            type="text"
            maxLength={80}
            value={settings.pngPrefix}
            disabled={disabled}
            onChange={(event) => update('pngPrefix', event.target.value)}
          />
        </label>
      )}
    </div>
  )
}
