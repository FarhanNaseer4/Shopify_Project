"""Tafelware price-tier JSON generation."""

from __future__ import annotations

import json
import os
import shutil
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from config.categories import CATEGORIES, CategoryConfig
from .transformer import sku_text
from .workbook_reader import read_records


TAFEL_PRICE_TIERS = (2, 4, 7, 10)
EXCLUDED_ZUSCHNITTE_SKUS = frozenset({"1272", "1503", "15790", "15791", "15792"})


def build_tafeln_price_data(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, float]], list[str]]:
    data: dict[str, dict[str, float]] = {}
    warnings: list[str] = []
    for record in records:
        sku = sku_text(record.get("Artikel-Nr"))
        tiers: dict[str, float] = {}
        for quantity in TAFEL_PRICE_TIERS:
            column = f"Preis {quantity}"
            value = record.get(column)
            if value in (None, ""):
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not Decimal(str(value)).is_finite():
                warnings.append(f"SKU {sku}: {column} is not numeric and was omitted from JSON.")
                continue
            tiers[str(quantity)] = float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        ordered = [record.get("Preis 1")] + list(tiers.values())
        if any(isinstance(a, (int, float)) and isinstance(b, (int, float)) and b > a
               for a, b in zip(ordered, ordered[1:])):
            warnings.append(f"SKU {sku}: quantity prices increase at a higher tier; source values retained for review.")
        if tiers:
            data[sku] = tiers
        else:
            warnings.append(f"SKU {sku}: no usable price tiers 2, 4, 7 or 10 for JSON.")
    return data, warnings


def build_zuschnitte_price_data(records: list[dict[str, Any]]) -> tuple[dict[str, int], list[str]]:
    data: dict[str, int] = {}
    warnings: list[str] = []
    for record in records:
        sku = sku_text(record.get("Artikel-Nr"))
        if sku in EXCLUDED_ZUSCHNITTE_SKUS:
            continue
        value = record.get("Preis")
        try:
            if isinstance(value, bool) or value in (None, ""):
                raise InvalidOperation
            if not Decimal(str(value)).is_finite():
                raise InvalidOperation
            rounded = int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        except (InvalidOperation, ValueError):
            warnings.append(f"SKU {sku}: Preis is not numeric and was omitted from JSON.")
            continue
        data[sku] = rounded
    return data, warnings


def _normalized(value: str) -> str:
    return unicodedata.normalize("NFC", value).casefold()


def find_group_source(config: CategoryConfig, source_dir: Path) -> Path:
    token = _normalized(config.source_filename_token)
    matches = [
        path for path in source_dir.glob("*.xlsx")
        if (token in _normalized(path.name) or
            (config.name == "Streckmetall" and "steckgitter" in _normalized(path.name)))
        and ".before-remove-" not in path.name and not path.name.startswith("~$")
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {config.group}/{config.name} source workbook "
            f"containing '{config.source_filename_token}' in {source_dir}; found {len(matches)}."
        )
    return matches[0]


def load_group_price_records(
    group: str,
    source_dir: Path,
    *,
    selected_category: str,
    selected_file: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Load all active categories, using the selected workbook as its override."""
    result: dict[str, list[dict[str, Any]]] = {}
    owners: dict[str, str] = {}
    for category, config in CATEGORIES[group].items():
        source = selected_file if category == selected_category else find_group_source(config, source_dir)
        records = read_records(source, config.source_sheet)
        if group == "Zuschnitte":
            records = [r for r in records if sku_text(r.get("Artikel-Nr")) not in EXCLUDED_ZUSCHNITTE_SKUS]
        result[category] = records
        for record in records:
            sku = sku_text(record.get("Artikel-Nr"))
            if not sku:
                raise ValueError(f"Blank SKU in consolidated {group} pricing source {source.name}.")
            if sku in owners:
                raise ValueError(
                    f"SKU {sku} occurs in both {owners[sku]} and {category}; "
                    f"cannot build consolidated {group} JSON."
                )
            owners[sku] = category
    return result


def build_consolidated_price_data(
    group: str,
    records_by_category: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[str]]:
    data: dict[str, Any] = {}
    warnings: list[str] = []
    for records in records_by_category.values():
        category_data, category_warnings = (
            build_tafeln_price_data(records)
            if group == "Tafeln"
            else build_zuschnitte_price_data(records)
        )
        data.update(category_data)
        warnings.extend(category_warnings)
    return dict(sorted(data.items(), key=lambda item: int(item[0]))), warnings


def consolidated_filename(group: str) -> str:
    return "tafelware_mr_json_values.json" if group == "Tafeln" else "quadratmeterpreise_zuschnitte_values.json"


def write_price_json(path: Path, data: dict[str, Any], backup_dir: Path) -> Path | None:
    """Validate, back up the prior master, then replace it atomically."""
    encoded = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(encoded)
    backup = None
    if path.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup = backup_dir / f"{path.stem}_{stamp}{path.suffix}"
        shutil.copy2(path, backup)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, path)
    return backup
