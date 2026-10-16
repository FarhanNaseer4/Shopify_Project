"""Image discovery and persistent Shopify filename baseline handling."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit


BASELINE_VERSION = 1


def image_filename(url: Any) -> str:
    """Return a case-insensitive filename, ignoring URL path and query changes."""
    value = "" if url is None else str(url).strip()
    if not value:
        return ""
    path = unquote(urlsplit(value).path).replace("\\", "/")
    return path.rsplit("/", 1)[-1].casefold()


def image_columns(record: dict[str, Any]) -> list[str]:
    """Return Bild, Bild 2, Bild 3... in gallery order."""
    matches: list[tuple[int, str]] = []
    for column in record:
        match = re.fullmatch(r"Bild(?:\s+(\d+))?", column, flags=re.IGNORECASE)
        if match:
            matches.append((int(match.group(1) or 1), column))
    return [column for _, column in sorted(matches)]


def record_images(records: Iterable[dict[str, Any]]) -> list[str]:
    """Return unique image URLs in stable source/gallery order."""
    result: list[str] = []
    seen: set[str] = set()
    for record in records:
        for column in image_columns(record):
            value = "" if record.get(column) is None else str(record[column]).strip()
            filename = image_filename(value)
            if value and filename and filename not in seen:
                result.append(value)
                seen.add(filename)
    return result


def load_baseline(path: Path) -> set[str]:
    if not path.is_file():
        raise ValueError(
            f"Image baseline is missing: {path}. Restore it or rebuild it from "
            "images already uploaded to Shopify."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != BASELINE_VERSION or not isinstance(data.get("filenames"), list):
        raise ValueError(f"Invalid image baseline format: {path}")
    return {str(value).casefold() for value in data["filenames"] if value}


def save_baseline(path: Path, filenames: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": BASELINE_VERSION,
        "description": "Image filenames confirmed as already uploaded to Shopify.",
        "filenames": sorted({name.casefold() for name in filenames if name}),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_records_to_baseline(path: Path, records: Iterable[dict[str, Any]]) -> int:
    existing = load_baseline(path) if path.exists() else set()
    updated = existing | {image_filename(url) for url in record_images(records)}
    save_baseline(path, updated)
    return len(updated - existing)


def save_pending_upload(
    path: Path,
    *,
    group: str,
    category: str,
    output_file: Path,
    image_urls: Iterable[str],
) -> int:
    """Persist images awaiting confirmation of a successful Shopify import."""
    filenames = sorted({image_filename(url) for url in image_urls if image_filename(url)})
    if not filenames:
        return 0
    existing_pending = load_pending_upload(path) if path.exists() else None
    existing_names = set(existing_pending.get("filenames", [])) if existing_pending else set()
    existing_outputs = list(existing_pending.get("output_files", [])) if existing_pending else []
    if existing_pending and not existing_outputs and existing_pending.get("output_file"):
        existing_outputs.append(existing_pending["output_file"])
    output_name = str(output_file)
    if output_name not in existing_outputs:
        existing_outputs.append(output_name)
    groups = set(existing_pending.get("groups", [])) if existing_pending else set()
    categories = set(existing_pending.get("categories", [])) if existing_pending else set()
    groups.add(group)
    categories.add(category)
    payload = {
        "version": BASELINE_VERSION,
        "groups": sorted(groups),
        "categories": sorted(categories),
        "output_files": existing_outputs,
        "filenames": sorted(existing_names | set(filenames)),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(set(filenames) - existing_names)


def load_pending_upload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != BASELINE_VERSION or not isinstance(data.get("filenames"), list):
        raise ValueError(f"Invalid pending image upload file: {path}")
    return data


def confirm_pending_upload(baseline_path: Path, pending_path: Path) -> int:
    """Add only emitted pending filenames to the baseline, then clear pending state."""
    pending = load_pending_upload(pending_path)
    if pending is None:
        return 0
    existing = load_baseline(baseline_path)
    pending_names = {str(value).casefold() for value in pending["filenames"] if value}
    save_baseline(baseline_path, existing | pending_names)
    pending_path.unlink()
    return len(pending_names - existing)
