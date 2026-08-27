# WAMI to Shopify / Matrixify Converter

This local application converts the supplied WAMI `.xlsx` exports into new Shopify/Matrixify `.xlsx` files. Original source and template workbooks are never modified.

## Install

Python 3.11 or newer is required.

### macOS

Open Terminal, navigate to this folder, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Choose the main category, subcategory, and corresponding workbook. Generated files are saved in `output/`; diagnostic logs are saved in `logs/`.

The generated Matrixify workbooks intentionally omit `Inventory Quantity`.
Rows containing an image use `Image Command = Replace`, and Tafeln format
options use the handles `kleinformat`, `mittelformat`, `grossformat`, and
`sonderformat`.

## Command-line mode

Useful for repeatable tests:

```bash
python main.py --group Tafeln --category Lochbleche --input input/WAMI_Tafeln/080426-Tafeln-Lochbleche.xlsx
```

Add `--dry-run` to validate without creating an output workbook.

## Current pricing note

For Tafeln, `Preis 1` is exported as `Variant Price`. Higher quantity tiers are reported in the log but are not exported because the referenced separate pricing-table format was not included in the supplied files.
