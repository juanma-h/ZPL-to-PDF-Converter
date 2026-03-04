# ZPL to PDF/PNG Converter (Desktop)

Aplicacion de escritorio para convertir archivos ZPL (`.txt`) a:

- un PDF con todas las etiquetas
- multiples PNG (una imagen por etiqueta)

## Funcionalidad incluida (MVP)

- Carga de archivo `.txt` con comandos ZPL
- Soporte para multiples etiquetas en el mismo archivo
- Selector de tamano de etiqueta (presets + personalizado)
- Selector de resolucion (`dpmm`)
- Exportacion a `PDF` o `PNG`
- Interfaz grafica sencilla con `PySide6`

## Requisitos

- Python 3.11+ recomendado
- Internet para renderizar etiquetas (usa la API de Labelary)

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar

```bash
python src/main.py
```

## Empaquetar para Windows (ejemplo)

Puedes generar un `.exe` con `PyInstaller`:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ZPLConverter src/main.py
```

El ejecutable quedara en `dist/ZPLConverter.exe`.

## Empaquetar para macOS M1 (siguiente fase)

- Recomendado construir en una Mac Apple Silicon para generar `.app` nativa
- Usar `pyinstaller` o `briefcase` en ese entorno
- El codigo actual ya es multiplataforma
