"""Deterministic Shopify display and handle transformations."""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any


MATERIAL_MAP = {
    "Aluminium (ohne Folie)": "aluminium-ohne-folie",
    "Aluminium ohne Folie": "aluminium-ohne-folie",
    "Edelstahl": "edelstahl",
    "Edelstahl (V2A)": "edelstahl",
    "Stahl": "stahl",
    "Stahl (verzinkt)": "stahl-verzinkt",
    "Sendzimir verzinkt": "stahl-verzinkt",
    "Stahl nachträglich feuerverzinkt": "stahl-feuerverzinkt",
    "PVC": "pvc",
    "Edelstahl (V2A) (beids. geschl. Korn 240)": "edelstahl-v-2-a-beids-geschl-korn-240",
    "Edelstahl (V2A) (ohne Folie)": "edelstahl-v-2-a-ohne-folie",
    "Edelstahl (V4A)": "edelstahl-v-4-a",
    "Aluminium (einseitig Folie)": "aluminium-einseitig-folie",
    "Stahl (eloverzinkt)": "stahl-eloverzinkt",
}


def text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def sku_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def slug(value: Any) -> str:
    result = text(value).lower().replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    result = unicodedata.normalize("NFKD", result).encode("ascii", "ignore").decode("ascii")
    result = re.sub(r"[^a-z0-9]+", "-", result)
    return result.strip("-")


def dimension_display(value: Any) -> str:
    # Display titles retain German decimal commas; slug() converts punctuation.
    return text(value)


def thickness_handle(value: Any) -> str:
    raw = text(value).lower().replace("mm", "").strip().replace(".", ",")
    try:
        number = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return slug(raw)
    rendered = format(number.normalize(), "f")
    return rendered.replace(".", "-")


def material_handle(value: Any, group: str = "Zuschnitte") -> str:
    raw = text(value)
    if raw == "Aluminium":
        return "aluminium-ohne-folie" if group == "Tafeln" else "aluminium"
    return MATERIAL_MAP.get(raw, slug(raw))


def format_handle(value: Any) -> str:
    raw = text(value)
    normalized = slug(raw)
    mappings = {
        "kleinformat": "kleinformat",
        "kleinformat-1000-x-2000-mm": "kleinformat",
        "mittelformat": "mittelformat",
        "mittelformat-1250-x-2500-mm": "mittelformat",
        "mittelformat-1500-x-2500-mm": "mittelformat",
        "grossformat": "grossformat",
        "grossformat-1500-x-3000-mm": "grossformat",
        "sonderformat": "sonderformat",
        "sonderformat-2000-x-3000-mm": "sonderformat",
    }
    return mappings.get(normalized, normalized)


def color_handle(value: Any) -> str:
    return slug(value)


def build_title(prefix: str, definition: Any, dimension: Any, include_definition: bool) -> str:
    definition_text = text(definition)
    dimension_text = dimension_display(dimension)
    # The completed Lochbleche template gives this WAMI combination a special
    # customer-facing name and removes the internal "Hv" code.
    if (
        prefix == "Lochblech Tafelware"
        and definition_text == "Sonderlochung"
        and dimension_text.startswith("Hexagonal - Hv ")
    ):
        title = f"{prefix} Hexagonallochung Hexagonal {dimension_text.removeprefix('Hexagonal - Hv ')}"
        return re.sub(r"\s*[-–—]\s*$", "", title).strip()
    parts = [prefix]
    if include_definition and definition_text:
        parts.append(definition_text)
    if dimension_text:
        parts.append(dimension_text)
    title = " ".join(parts)
    # Remove WAMI separators that occur at the end of some product names, while
    # preserving hyphens and dashes used inside the title.
    return re.sub(r"\s*[-–—]\s*$", "", title).strip()


def build_handle(title: str) -> str:
    return slug(title)
