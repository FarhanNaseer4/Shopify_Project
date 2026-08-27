"""Core WAMI to Shopify/Matrixify conversion service."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from config.categories import CategoryConfig, get_category
from .transformer import (build_handle, build_title, color_handle, format_handle,
                          material_handle, sku_text, text, thickness_handle)
from .workbook_reader import extract_headers, find_template, read_records


@dataclass(frozen=True)
class ConversionResult:
    group: str
    category: str
    input_rows: int
    products: int
    variants: int
    warnings: tuple[str, ...]
    output_file: Path | None
    log_file: Path


META_FIELDS = {
    "Material-Gruppe": "Variant Metafield: custom.td_material_gruppe [single_line_text_field]",
    "DIN-Bezeichnung (alt)": "Variant Metafield: custom.td_din_bezeichnung_alt [single_line_text_field]",
    "DIN-Bezeichnung (neu)": "Variant Metafield: custom.td_din_bezeichnung_neu [single_line_text_field]",
    "SpezifischesGewicht": "Variant Metafield: custom.td_spezifisches_gewicht [single_line_text_field]",
    "Gewicht pro Tafel": "Variant Metafield: custom.gewicht_pro_tafel [single_line_text_field]",
    "Gewicht pro m²": "Variant Metafield: custom.td_gewicht_pro_m2 [single_line_text_field]",
    "DIN": "Variant Metafield: custom.td_din [single_line_text_field]",
    "Lagerplatz": "Variant Metafield: custom.lagerplatz [single_line_text_field]",
    "Untertitel": "Variant Metafield: custom.untertitel [single_line_text_field]",
    "Toleranzen": "Variant Metafield: custom.toleranzen [single_line_text_field]",
    "Drahtüberstände": "Variant Metafield: custom.drahtuberstande [single_line_text_field]",
}


def _required(config: CategoryConfig) -> set[str]:
    fields = {"Def-Lochung", "Material", config.thickness_column, "Artikel-Nr", "Bild", config.hint_column}
    if config.dimension_column:
        fields.add(config.dimension_column)
    if config.group == "Tafeln":
        fields.update(("Format", "Preis 1"))
    else:
        fields.add("Preis")
    if "Farbe" in config.options:
        fields.add("Farbe")
    return fields


def _group_key(row: dict[str, Any], config: CategoryConfig) -> tuple[str, str]:
    return text(row.get("Def-Lochung")), text(row.get(config.dimension_column)) if config.dimension_column else ""


def _option_value(option: str, row: dict[str, Any], config: CategoryConfig) -> str:
    if option == "Material": return material_handle(row.get("Material"), config.group)
    if option == "Stärke": return thickness_handle(row.get(config.thickness_column))
    if option == "Format": return format_handle(row.get("Format"))
    if option == "Farbe": return color_handle(row.get("Farbe"))
    return ""


def _linked_to(option: str) -> str:
    return {"Material": "product.metafields.custom.material", "Stärke": "product.metafields.custom.starke", "Format": "product.metafields.custom.format_tafel", "Farbe": "product.metafields.shopify.color-pattern"}[option]


def _build_rows(records: list[dict[str, Any]], headers: list[str], config: CategoryConfig, warnings: list[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen_images: dict[tuple[str, str], set[str]] = {}
    for source in records:
        key = _group_key(source, config)
        title = build_title(config.title_prefix, key[0], key[1], config.include_definition)
        row = {header: None for header in headers}
        row.update({"Handle": build_handle(title), "Command": "MERGE", "Title": title, "Variant Command": "MERGE", "Variant SKU": sku_text(source.get("Artikel-Nr"))})
        image = text(source.get("Bild"))
        images = seen_images.setdefault(key, set())
        if image and image not in images:
            row["Image Src"] = image
            row["Image Command"] = "Replace"
            images.add(image)
        for index, option in enumerate(config.options, 1):
            label = "Format Tafel" if option == "Format" else option
            row[f"Option{index} Name"] = label
            row[f"Option{index} Value"] = _option_value(option, source, config)
            row[f"Option{index} Linked To"] = _linked_to(option)
        if config.group == "Tafeln":
            price = source.get("Preis 1")
            row["Variant Price"] = round(float(price), 2) if isinstance(price, (int, float)) else price
            tiers = [name for name in source if name.startswith("Preis ") and name != "Preis 1" and source.get(name) not in (None, "")]
            if tiers:
                warning = f"Quantity tiers {', '.join(tiers)} were detected but not exported (separate tier format not supplied)."
                if warning not in warnings:
                    warnings.append(warning)
        else:
            price = source.get("Preis")
            row["Variant Price"] = 18.99
            if isinstance(price, (int, float)) and price:
                row["Unit Price Total Measure"] = round(18.99 / (float(price) / 100), 3)
            else:
                warnings.append(f"SKU {row['Variant SKU']}: invalid Preis; unit price measure is blank.")
            row["Unit Price Total Measure Unit"] = "M2"
            row["Unit Price Base Measure"] = 1
            row["Unit Price Base Measure Unit"] = "M2"
        for source_name, destination in META_FIELDS.items():
            if destination in row:
                row[destination] = source.get(source_name)
        hint_dest = "Variant Metafield: custom.td_hinweis [single_line_text_field]"
        if hint_dest in row: row[hint_dest] = source.get(config.hint_column)
        if config.area_column:
            suffix = {"Ao, gelochte Fläche": "custom.td_ao_gelochte_flache", "Ao, ungelochte Fläche": "custom.ao_ungelochte_flache", "Geprägte Fläche": "custom.gepragte_flache", "Freie Fläche": "custom.freie_flache"}[config.area_column]
            destination = f"Variant Metafield: {suffix} [single_line_text_field]"
            if destination in row: row[destination] = source.get(config.area_column)
        output.append(row)
    return output


def convert_wawi_to_shopify(*, group: str, category: str, input_file: Path, templates_dir: Path, output_dir: Path, logs_dir: Path, dry_run: bool = False) -> ConversionResult:
    config = get_category(group, category)
    input_file, templates_dir, output_dir, logs_dir = map(Path, (input_file, templates_dir, output_dir, logs_dir))
    if input_file.suffix.lower() != ".xlsx" or not input_file.is_file():
        raise ValueError("Input must be an existing .xlsx workbook.")
    expected_parent = f"WAMI_{group}"
    if input_file.parent.name != expected_parent:
        raise ValueError(f"The selected file must be inside '{expected_parent}'.")
    template = find_template(group, templates_dir)
    headers = extract_headers(template, config.template_sheet)
    records = read_records(input_file, config.source_sheet)
    missing = sorted(_required(config) - set(records[0]))
    if missing:
        raise ValueError("Selected workbook does not match the category. Missing columns: " + ", ".join(missing))
    skus = [sku_text(row.get("Artikel-Nr")) for row in records]
    blank = sum(not sku for sku in skus)
    duplicates = sorted(sku for sku, count in Counter(skus).items() if sku and count > 1)
    if blank: raise ValueError(f"Input contains {blank} blank SKU value(s).")
    if duplicates: raise ValueError("Duplicate SKU value(s): " + ", ".join(duplicates[:20]))
    # Microseconds prevent a rapid repeated run from overwriting output or logs.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"run_{stamp}.log"
    logging.basicConfig(filename=log_file, level=logging.INFO, force=True, format="%(asctime)s %(levelname)s %(message)s")
    warnings: list[str] = []
    rows = _build_rows(records, headers, config, warnings)
    if [*rows[0]] != headers: raise RuntimeError("Internal output header order differs from template.")
    output_file = None
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"shopify_{group}_{category}_{stamp}.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = config.template_sheet
        ws.append(headers)
        for row in rows: ws.append([row[h] for h in headers])
        wb.save(output_file)
    products = len({_group_key(row, config) for row in records})
    logging.info("group=%s category=%s input=%s template=%s rows=%d products=%d warnings=%d output=%s", group, category, input_file, template, len(records), products, len(warnings), output_file)
    return ConversionResult(group, category, len(records), products, len(rows), tuple(warnings), output_file, log_file)
