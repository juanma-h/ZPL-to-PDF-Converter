from __future__ import annotations

import re

from .models import ZplDocumentStats


LABEL_PATTERN = re.compile(r"\^XA[\s\S]*?\^XZ", re.IGNORECASE)
QUANTITY_PATTERN = re.compile(r"\^PQ\s*([0-9]+)", re.IGNORECASE)


def split_zpl_labels(zpl_text: str) -> list[str]:
    direct_matches = [chunk.strip() for chunk in LABEL_PATTERN.findall(zpl_text) if chunk.strip()]
    if direct_matches:
        return direct_matches

    raw = zpl_text.strip()
    if not raw:
        return []

    if re.search(r"\^XZ", raw, re.IGNORECASE):
        chunks = [chunk.strip() for chunk in re.split(r"\^XZ", raw, flags=re.IGNORECASE) if chunk.strip()]
        labels: list[str] = []
        for chunk in chunks:
            with_xa = chunk if re.search(r"\^XA", chunk, re.IGNORECASE) else f"^XA\n{chunk}"
            labels.append(f"{with_xa}\n^XZ")
        return labels

    with_xa = raw if re.search(r"\^XA", raw, re.IGNORECASE) else f"^XA\n{raw}"
    return [f"{with_xa}\n^XZ"]


def extract_quantity_from_label(label: str) -> int:
    match = QUANTITY_PATTERN.search(label)
    if not match:
        return 1

    try:
        qty = int(match.group(1))
    except ValueError:
        return 1

    return qty if qty > 0 else 1


def analyze_zpl_text(zpl_text: str) -> ZplDocumentStats:
    labels = split_zpl_labels(zpl_text)
    total_quantity = sum(extract_quantity_from_label(label) for label in labels)
    has_quantity_commands = any(QUANTITY_PATTERN.search(label) for label in labels)
    return ZplDocumentStats(
        label_count=len(labels),
        total_quantity=total_quantity,
        has_quantity_commands=has_quantity_commands,
    )
