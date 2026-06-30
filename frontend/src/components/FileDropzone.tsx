import { useRef, useState } from 'react'

interface FileDropzoneProps {
  file: File | null
  disabled?: boolean
  onSelect: (file: File) => void
  onClear: () => void
}

export function FileDropzone({ file, disabled, onSelect, onClear }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  function acceptFileList(files: FileList | null): void {
    const selected = files?.[0]
    if (selected) onSelect(selected)
  }

  return (
    <div
      className={`dropzone ${dragging ? 'dropzone--active' : ''} ${file ? 'dropzone--ready' : ''}`}
      onDragEnter={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault()
        setDragging(false)
        acceptFileList(event.dataTransfer.files)
      }}
    >
      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept=".txt,.zpl,text/plain"
        disabled={disabled}
        onChange={(event) => acceptFileList(event.target.files)}
      />
      <div className="dropzone__icon" aria-hidden="true">
        {file ? '✓' : 'ZPL'}
      </div>
      {file ? (
        <>
          <strong>{file.name}</strong>
          <span>{(file.size / 1024).toFixed(1)} KB</span>
          <button className="button button--ghost" type="button" onClick={onClear}>
            Cambiar archivo
          </button>
        </>
      ) : (
        <>
          <strong>Arrastra tu archivo ZPL</strong>
          <span>Formatos .txt y .zpl, hasta 10 MB</span>
          <button
            className="button button--secondary"
            type="button"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            Seleccionar archivo
          </button>
        </>
      )}
    </div>
  )
}
