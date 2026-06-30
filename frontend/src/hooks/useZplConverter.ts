import { useEffect, useState } from 'react'

import { analyzeZpl, convertZpl, downloadBlob, getHealth } from '../api/client'
import type {
  AnalyzeResponse,
  ConversionSettings,
  DownloadResult,
  HealthResponse,
} from '../types/api'

type RequestStatus = 'idle' | 'analyzing' | 'converting' | 'success' | 'error'

export function useZplConverter() {
  const [file, setFile] = useState<File | null>(null)
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [status, setStatus] = useState<RequestStatus>('idle')
  const [message, setMessage] = useState('Selecciona un archivo ZPL para comenzar.')
  const [lastResult, setLastResult] = useState<DownloadResult | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getHealth(controller.signal)
      .then(setHealth)
      .catch(() => setHealth(null))
    return () => controller.abort()
  }, [])

  async function selectFile(selectedFile: File): Promise<void> {
    setFile(selectedFile)
    setAnalysis(null)
    setLastResult(null)
    setStatus('analyzing')
    setMessage('Analizando el archivo...')
    try {
      const result = await analyzeZpl(selectedFile)
      setAnalysis(result)
      setStatus('idle')
      setMessage('Archivo listo para convertir.')
    } catch (error) {
      setStatus('error')
      setMessage(error instanceof Error ? error.message : 'No se pudo analizar el archivo.')
    }
  }

  function clearFile(): void {
    setFile(null)
    setAnalysis(null)
    setLastResult(null)
    setStatus('idle')
    setMessage('Selecciona un archivo ZPL para comenzar.')
  }

  async function convert(settings: ConversionSettings): Promise<void> {
    if (!file) return
    setStatus('converting')
    setMessage('Renderizando y preparando la descarga...')
    try {
      const result = await convertZpl(file, settings)
      setLastResult(result)
      downloadBlob(result)
      setStatus('success')
      setMessage(
        `Conversion completada: ${result.renderedLabels} etiquetas en ${result.generatedFiles} archivo(s).`,
      )
    } catch (error) {
      setStatus('error')
      setMessage(error instanceof Error ? error.message : 'No se pudo completar la conversion.')
    }
  }

  function downloadAgain(): void {
    if (lastResult) downloadBlob(lastResult)
  }

  return {
    file,
    analysis,
    health,
    status,
    message,
    lastResult,
    selectFile,
    clearFile,
    convert,
    downloadAgain,
  }
}
