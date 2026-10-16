"""Core WAMI to Shopify/Matrixify conversion service."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from decimal import Decimal, ROUND_HALF_UP

from openpyxl import Workbook

from config.categories import CategoryConfig, get_category
from .transformer import (build_handle, build_title, color_handle, format_handle,
                          material_handle, sku_text, text, thickness_handle)
from .workbook_reader import extract_headers, find_template, read_records
from .images import image_filename, load_baseline, record_images, save_pending_upload
from .pricing import (EXCLUDED_ZUSCHNITTE_SKUS, build_consolidated_price_data, consolidated_filename,
                      load_group_price_records, write_price_json)


@dataclass(frozen=True)
class ConversionResult:
    group: str
    category: str
    input_rows: int
    products: int
    variants: int
    warnings: tuple[str, ...]
    output_file: Path | None
    price_json_file: Path | None
    pending_images: int
    log_file: Path
    new_products_file: Path | None = None
    new_variants: int = 0


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
    fields = {"Def-Lochung", "Material", config.thickness_column, "Artikel-Nr"}
    if config.dimension_column and config.name != "Duett":
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


def _validate_variant_combinations(records: list[dict[str, Any]], config: CategoryConfig) -> None:
    combinations: dict[tuple[tuple[str, str], tuple[str, ...]], list[str]] = defaultdict(list)
    for record in records:
        values = tuple(_option_value(option, record, config) for option in config.options)
        combinations[(_group_key(record, config), values)].append(sku_text(record.get("Artikel-Nr")))
    duplicates = [(key, values, skus) for (key, values), skus in combinations.items() if len(skus) > 1]
    if duplicates:
        details = []
        for key, values, skus in duplicates[:10]:
            details.append(
                f"product {' / '.join(key)}; options {' / '.join(values)}; SKUs {', '.join(skus)}"
            )
        raise ValueError("Duplicate Shopify variant option combination(s): " + " | ".join(details))


def _build_rows(records: list[dict[str, Any]], headers: list[str], config: CategoryConfig, warnings: list[str], image_baseline: set[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    grouped_images: dict[tuple[str, str], list[str]] = defaultdict(list)
    grouped_seen: dict[tuple[str, str], set[str]] = defaultdict(set)
    for source in records:
        key = _group_key(source, config)
        for image in record_images([source]):
            filename = image_filename(image)
            if filename not in grouped_seen[key]:
                grouped_images[key].append(image)
                grouped_seen[key].add(filename)
    emitted_products: set[tuple[str, str]] = set()
    for source in records:
        key = _group_key(source, config)
        title = build_title(config.title_prefix, key[0], key[1], config.include_definition)
        row = {header: None for header in headers}
        row.update({"Handle": build_handle(title), "Command": "MERGE", "Title": title, "Variant Command": "MERGE", "Variant SKU": sku_text(source.get("Artikel-Nr"))})
        is_product_header = key not in emitted_products
        changed_images = [
            (position, url)
            for position, url in enumerate(grouped_images[key], start=1)
            if image_filename(url) not in image_baseline
        ]
        changed_primary = next(((position, url) for position, url in changed_images if position == 1), None)
        if is_product_header and changed_primary:
            row["Image Src"] = changed_primary[1]
            row["Image Position"] = changed_primary[0]
            row["Image Command"] = "Replace"
        for index, option in enumerate(config.options, 1):
            label = option
            row[f"Option{index} Name"] = label
            row[f"Option{index} Value"] = _option_value(option, source, config)
            row[f"Option{index} Linked To"] = _linked_to(option)
        if config.group == "Tafeln":
            price = source.get("Preis 1")
            row["Variant Price"] = round(float(price), 2) if isinstance(price, (int, float)) else price
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
        if is_product_header:
            for position, image in changed_images:
                if position == 1:
                    continue
                gallery_row = {header: None for header in headers}
                gallery_row["Handle"] = row["Handle"]
                gallery_row["Image Src"] = image
                gallery_row["Image Position"] = position
                gallery_row["Image Command"] = "Replace"
                output.append(gallery_row)
            emitted_products.add(key)
    return output


def _current_rows(records, headers, config, reference, warnings):
    """Use Shopify's SKU/handle reference for updates; keep creation fields separate."""
    excluded = EXCLUDED_ZUSCHNITTE_SKUS if config.group == "Zuschnitte" else set()
    records = [r for r in records if sku_text(r.get("Artikel-Nr")) not in excluded]
    known = {sku_text(r.get("Variant SKU")): r for r in reference if r.get("Variant SKU")}
    if len(known) != sum(bool(r.get("Variant SKU")) for r in reference):
        raise ValueError("Reference template contains duplicate SKUs; refresh the Shopify reference before converting.")
    if any(not text(r.get("Handle")) or text(r.get("Handle")).startswith("#") for r in known.values()):
        raise ValueError("Reference template contains missing or invalid Shopify handles.")
    known_handles = {text(r.get("Handle")) for r in known.values()}
    updates, additions = [], []
    creation_headers = ["Handle", "Command", "Title", "Variant Command", "Variant SKU", "Variant Price"]
    for i in range(1, len(config.options) + 1):
        creation_headers.extend([f"Option{i} Name", f"Option{i} Value", f"Option{i} Linked To"])
    for source in records:
        sku = sku_text(source.get("Artikel-Nr"))
        previous = known.get(sku)
        source_handle = text(source.get("Handle"))
        if previous:
            handle = text(previous.get("Handle"))
            if source_handle != handle:
                warnings.append(f"SKU {sku}: WAWI handle '{source_handle}' differs; using Shopify reference '{handle}'.")
            # Retain template values when a source cell is missing; never clear
            # existing reference metafields through an incidental blank cell.
            row = {h: previous.get(h) for h in headers}
            row.update({"Handle": handle, "Command": "UPDATE", "Variant Command": "UPDATE", "Variant SKU": sku})
        else:
            dimension = text(source.get(config.dimension_column)) if config.dimension_column else ""
            if config.name == "Duett":
                dimension = text(source.get("Produkt"))
            title = build_title(config.title_prefix, text(source.get("Def-Lochung")), dimension, config.include_definition)
            handle = source_handle if source_handle and not source_handle.startswith("#") else build_handle(title)
            row = {h: None for h in dict.fromkeys(creation_headers + headers)}
            row.update({"Handle": handle, "Command": "UPDATE" if handle in known_handles else "NEW",
                        "Title": None if handle in known_handles else title,
                        "Variant Command": "NEW", "Variant SKU": sku})
            for i, option in enumerate(config.options, 1):
                row.update({f"Option{i} Name": option, f"Option{i} Value": _option_value(option, source, config),
                            f"Option{i} Linked To": _linked_to(option)})
            if config.group == "Zuschnitte":
                row["Variant Price"] = 18.99
        if config.group == "Tafeln":
            price = source.get("Preis 1")
            if isinstance(price, bool) or not isinstance(price, (int, float)) or not Decimal(str(price)).is_finite():
                raise ValueError(f"SKU {sku}: Preis 1 must be a finite numeric value.")
            row["Variant Price"] = float(Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        mapping = dict(META_FIELDS)
        mapping[config.hint_column] = "Variant Metafield: custom.td_hinweis [single_line_text_field]"
        if config.area_column:
            suffix = {"Ao, gelochte Fläche": "td_ao_gelochte_flache", "Ao, ungelochte Fläche": "ao_ungelochte_flache",
                      "Geprägte Fläche": "gepragte_flache", "Freie Fläche": "freie_flache"}[config.area_column]
            mapping[config.area_column] = f"Variant Metafield: custom.{suffix} [single_line_text_field]"
        for name, destination in mapping.items():
            if destination in row and source.get(name) not in (None, ""):
                row[destination] = source[name]
        for h in list(row):
            if h.startswith("Image ") or h.startswith("Unit Price ") or "produktdatenblatt" in h or h == "Inventory Quantity":
                del row[h]
            elif config.group == "Tafeln" and "drahtuberstande" in h:
                del row[h]
        (updates if previous else additions).append(row)
    for collection in (updates, additions):
        collection.sort(key=lambda r: r["Handle"])
    return updates, additions


def _write_products(path, rows):
    headers = list(dict.fromkeys(h for row in rows for h in row))
    headers = [h for h in headers if any(row.get(h) not in (None, "") for row in rows)]
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])
    ws.freeze_panes = "A2"
    wb.save(path)


def convert_wawi_to_shopify(*, group: str, category: str, input_file: Path, templates_dir: Path, output_dir: Path, logs_dir: Path, dry_run: bool = False, image_baseline_file: Path | None = None, pending_image_file: Path | None = None) -> ConversionResult:
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
    if group == "Zuschnitte":
        records = [r for r in records if sku_text(r.get("Artikel-Nr")) not in EXCLUDED_ZUSCHNITTE_SKUS]
    if not records:
        raise ValueError("No active product rows remain after applying the confirmed SKU exclusions.")
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
    reference = read_records(template, config.template_sheet)
    rows, new_rows = _current_rows(records, headers, config, reference, warnings)
    known_rows = {row["Variant SKU"]: row for row in rows}
    existing_combinations = set()
    for source in records:
        known = known_rows.get(sku_text(source.get("Artikel-Nr")))
        if known:
            existing_combinations.add((known["Handle"], tuple(_option_value(o, source, config) for o in config.options)))
    combinations = set()
    for row in new_rows:
        key = (row["Handle"], tuple(row.get(f"Option{i} Value") for i in range(1, len(config.options) + 1)))
        if key in combinations or key in existing_combinations:
            raise ValueError(f"Duplicate new variant option combination: {key}")
        combinations.add(key)
    output_file = None
    price_json_file = None
    pending_images = 0
    new_products_file = None
    group_records = load_group_price_records(
        group,
        input_file.parent,
        selected_category=category,
        selected_file=input_file,
    )
    price_data, price_warnings = build_consolidated_price_data(group, group_records)
    warnings.extend(price_warnings)
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"shopify_{group}_{category}_{stamp}.xlsx"
        if rows:
            _write_products(output_file, rows)
        else:
            output_file = None
        if new_rows:
            new_products_file = output_dir / f"shopify_{group}_{category}_NEW_{stamp}.xlsx"
            _write_products(new_products_file, new_rows)
        price_json_file = output_dir / consolidated_filename(group)
        write_price_json(
            price_json_file,
            price_data,
            Path(__file__).resolve().parents[1] / "backups" / "generated_prices",
        )
    products = len({row['Handle'] for row in rows + new_rows})
    for warning in warnings:
        logging.warning(warning)
    logging.info("group=%s category=%s input=%s template=%s rows=%d products=%d warnings=%d output=%s price_json=%s pending_images=%d", group, category, input_file, template, len(records), products, len(warnings), output_file, price_json_file, pending_images)
    return ConversionResult(group, category, len(records), products, len(records), tuple(warnings), output_file, price_json_file, pending_images, log_file, new_products_file, len(new_rows))
