import fs from "node:fs/promises";
import path from "node:path";
import { ready } from "zpl-renderer-js";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      continue;
    }

    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      throw new Error(`Falta valor para --${key}`);
    }
    args[key] = next;
    i += 1;
  }
  return args;
}

function requireArg(args, key) {
  const value = args[key];
  if (!value) {
    throw new Error(`Argumento requerido: --${key}`);
  }
  return value;
}

function parsePositiveNumber(raw, key) {
  const num = Number(raw);
  if (!Number.isFinite(num) || num <= 0) {
    throw new Error(`Valor invalido para --${key}: ${raw}`);
  }
  return num;
}

function normalizeBase64List(rawResult) {
  if (Array.isArray(rawResult)) {
    return rawResult;
  }
  if (typeof rawResult === "string" && rawResult.length > 0) {
    return [rawResult];
  }
  return [];
}

function splitZplLabels(zplText) {
  const regex = /\^XA[\s\S]*?\^XZ/gi;
  const directMatches = zplText.match(regex);
  if (directMatches && directMatches.length > 0) {
    return directMatches.map((chunk) => chunk.trim()).filter(Boolean);
  }

  const raw = zplText.trim();
  if (!raw) {
    return [];
  }

  if (/\^XZ/i.test(raw)) {
    return raw
      .split(/\^XZ/i)
      .map((chunk) => chunk.trim())
      .filter(Boolean)
      .map((chunk) => {
        const withXa = /\^XA/i.test(chunk) ? chunk : `^XA\n${chunk}`;
        return `${withXa}\n^XZ`;
      });
  }

  const withXa = /\^XA/i.test(raw) ? raw : `^XA\n${raw}`;
  return [`${withXa}\n^XZ`];
}

function removeDataUrlPrefix(base64) {
  const marker = "base64,";
  const index = base64.indexOf(marker);
  if (index === -1) {
    return base64.trim();
  }
  return base64.slice(index + marker.length).trim();
}

function extractQuantityFromLabel(label) {
  const match = label.match(/\^PQ\s*([0-9]+)/i);
  if (!match) {
    return 1;
  }

  const qty = Number.parseInt(match[1], 10);
  if (!Number.isFinite(qty) || qty <= 0) {
    return 1;
  }
  return qty;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inputPath = path.resolve(requireArg(args, "input"));
  const outputDir = path.resolve(requireArg(args, "output-dir"));
  const prefix = requireArg(args, "prefix");

  const widthMm = parsePositiveNumber(requireArg(args, "width-mm"), "width-mm");
  const heightMm = parsePositiveNumber(requireArg(args, "height-mm"), "height-mm");
  const dpmm = parsePositiveNumber(requireArg(args, "dpmm"), "dpmm");

  const zpl = await fs.readFile(inputPath, "utf8");
  if (!zpl.trim()) {
    throw new Error("El archivo de entrada esta vacio.");
  }

  await fs.mkdir(outputDir, { recursive: true });
  const labels = splitZplLabels(zpl);
  if (labels.length === 0) {
    throw new Error("No se encontraron etiquetas ZPL validas en el archivo.");
  }

  const { api } = await ready;
  const images = [];
  for (const label of labels) {
    const quantity = extractQuantityFromLabel(label);
    const base64 = api.Render(label, widthMm, heightMm, dpmm);
    for (let i = 0; i < quantity; i += 1) {
      images.push(base64);
    }
  }
  const normalizedImages = normalizeBase64List(images);

  if (normalizedImages.length === 0) {
    throw new Error("El renderer no produjo imagenes.");
  }

  const files = [];
  for (let i = 0; i < normalizedImages.length; i += 1) {
    const fileName = `${prefix}_${String(i + 1).padStart(4, "0")}.png`;
    const filePath = path.join(outputDir, fileName);
    const cleanBase64 = removeDataUrlPrefix(normalizedImages[i]);
    const buffer = Buffer.from(cleanBase64, "base64");
    await fs.writeFile(filePath, buffer);
    files.push(filePath);
  }

  console.log(
    JSON.stringify({
      count: files.length,
      files,
    }),
  );
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
