import { useState } from 'react'

import { FileDropzone } from './components/FileDropzone'
import { MaterialPreview } from './components/MaterialPreview'
import { SettingsPanel } from './components/SettingsPanel'
import { StatsGrid } from './components/StatsGrid'
import { useZplConverter } from './hooks/useZplConverter'
import type { ConversionSettings } from './types/api'

const initialSettings: ConversionSettings = {
  outputFormat: 'pdf',
  widthIn: 4,
  heightIn: 6,
  dpmm: 12,
  qualityScale: 2,
  channelsPerRow: 1,
  dieCutEnabled: true,
  dieCutMarginMm: 5,
  dieCutColumns: 2,
  pngPrefix: 'etiqueta',
}

export default function App() {
  const [settings, setSettings] = useState(initialSettings)
  const converter = useZplConverter()
  const busy = converter.status === 'analyzing' || converter.status === 'converting'
  const runtimeAvailable = converter.health?.runtime.available !== false

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="ZPL Converter">
          <span className="brand__mark">Z</span>
          <span>
            <strong>ZPL Converter</strong>
            <small>PDF & PNG</small>
          </span>
        </a>
        <div className={`runtime ${runtimeAvailable ? 'runtime--ok' : 'runtime--error'}`}>
          <span />
          {converter.health?.runtime.description ?? 'Comprobando motor...'}
        </div>
      </header>

      <main>
        <section className="hero">
          <div>
            <h1>De ZPL a un archivo listo para usar.</h1>
            <p>
              Carga tus etiquetas, ajusta el formato y descarga un PDF o paquete PNG 
            </p>
          </div>
        </section>

        <div className="workspace">
          <section className="column">
            <article className="card">
              <div className="card__heading">
                <span className="step">1</span>
                <div>
                  <h2>Archivo de entrada</h2>
                  <p>Selecciona el documento que contiene tus comandos ZPL</p>
                </div>
              </div>
              <FileDropzone
                file={converter.file}
                disabled={busy}
                onSelect={(file) => void converter.selectFile(file)}
                onClear={converter.clearFile}
              />
              <StatsGrid analysis={converter.analysis} settings={settings} />
            </article>

            <article className="card">
              <div className="card__heading">
                <span className="step">2</span>
                <div>
                  <h2>Configuracion</h2>
                  <p>Define tamaño, calidad, formato.</p>
                </div>
              </div>
              <SettingsPanel settings={settings} disabled={busy} onChange={setSettings} />
            </article>
          </section>

          <aside className="column column--sticky">
            <article className="card card--preview">
              <MaterialPreview settings={settings} />
              <div className={`status status--${converter.status}`} role="status">
                {busy && <span className="spinner" aria-hidden="true" />}
                <p>{converter.message}</p>
              </div>
              <button
                className="button button--primary button--large"
                type="button"
                disabled={!converter.file || !converter.analysis || busy || !runtimeAvailable}
                onClick={() => void converter.convert(settings)}
              >
                {converter.status === 'converting'
                  ? 'Procesando...'
                  : `Convertir a ${settings.outputFormat.toUpperCase()}`}
              </button>
              {converter.lastResult && (
                <button className="button button--ghost" type="button" onClick={converter.downloadAgain}>
                  Descargar de nuevo
                </button>
              )}
              <div className="privacy-note">
                <span aria-hidden="true">◆</span>
                <p>
                  <strong>Procesamiento privado</strong>
                  Los archivos temporales se eliminan al finalizar la descarga.
                </p>
              </div>
            </article>
          </aside>
        </div>
      </main>

      <footer>
        <span>ZPL Converter v{converter.health?.version ?? '3.0.0'}</span>
        <a href="/api/v1/docs" target="_blank" rel="noreferrer">API</a>
      </footer>
    </div>
  )
}
