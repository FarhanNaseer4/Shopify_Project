"""Command-line entry point for repeatable conversion and testing."""

from __future__ import annotations

import argparse
from pathlib import Path

from config.categories import CATEGORIES
from src import convert_wawi_to_shopify

ROOT = Path(__file__).resolve().parent


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Convert WAMI Excel exports to Shopify/Matrixify Excel files.")
    result.add_argument("--group", choices=sorted(CATEGORIES), required=True)
    result.add_argument("--category", required=True)
    result.add_argument("--input", type=Path, required=True)
    result.add_argument("--dry-run", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = convert_wawi_to_shopify(group=args.group, category=args.category, input_file=args.input.resolve(), templates_dir=ROOT / "input" / "Templates", output_dir=ROOT / "output", logs_dir=ROOT / "logs", dry_run=args.dry_run)
    except (ValueError, OSError) as exc:
        print(f"Conversion failed: {exc}")
        return 1
    print(f"Processing complete.\nGroup: {result.group}\nCategory: {result.category}\nInput rows: {result.input_rows}\nProducts: {result.products}\nVariants: {result.variants}\nWarnings: {len(result.warnings)}\nExcel output: {result.output_file or 'dry run'}\nConsolidated price JSON: {result.price_json_file or 'dry run'}\nPending images: {result.pending_images}\nLog: {result.log_file}")
    if result.new_products_file:
        print(f"New products/variants: {result.new_products_file}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
