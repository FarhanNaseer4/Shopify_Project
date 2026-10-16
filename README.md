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
Tafeln Option 3 is named `Format`, remains linked to
`product.metafields.custom.format_tafel`, and uses the handles `kleinformat`,
`mittelformat`, `grossformat`, and `sonderformat`.

Images and PDFs are managed manually in Shopify. All image fields, image
commands, PDF references and Unit Price columns are omitted from generated
files. The image confirmation button is no longer used.

Each category update workbook has a sheet named `Products`. Existing SKUs use
the Shopify reference template's handle and UPDATE commands. Current WAWI
prices and technical fields are mapped to the reference template columns.
Missing source technical values retain the reference value when available.
Entirely empty columns are removed. Existing titles and options are not changed.

SKUs absent from the reference template go into a separate `_NEW_` workbook
with creation fields. This keeps empty title/option cells out of update files.
New products use NEW; additions to known products use UPDATE with Variant
Command NEW. Review these files before importing. After successful creation,
refresh the Shopify reference template before the next conversion. Generating
a file does not mark it as imported; repeated NEW imports can fail.

The local folder structure is unchanged. Replace the updated category workbook
in `input/WAMI_Tafeln/` or `input/WAMI_Zuschnitte/`; keep the other category
files in place. Move archived versions outside these folders. No Google Drive
integration is required. The original WAWI worksheet names are supported.

Prägeblech is excluded from Tafelware. Confirmed obsolete Zuschnitte SKUs
1272, 1503, 15790, 15791 and 15792 are excluded even if reintroduced into WAWI.
Omitting these SKUs does not delete live Shopify products.

## Command-line mode

Useful for repeatable tests:

```bash
python main.py --group Tafeln --category Lochbleche --input input/WAMI_Tafeln/261012-Tafeln-Lochbleche-Marc.xlsx
```

Add `--dry-run` to validate without creating an output workbook.

## Consolidated price JSON files

Every conversion rebuilds one consolidated price file for its complete product
group from the current workbooks in that group's input folder. The workbook
selected in the app overrides the corresponding local category source.

For Tafeln, the output is `output/tafelware_mr_json_values.json`. `Preis 1`
remains the Excel `Variant Price`; the JSON contains only quantity tiers 2, 4,
7, and 10. Only the four active categories are included: Lochbleche,
Streckmetall, Schweißgitter, and Wellengitter.

Tafeln prices are commercially rounded to two decimal places. Increasing
quantity prices produce warnings and retain source values for client review.
JSON numbers such as 70.0 and 70.00 have the same numeric value.

For Zuschnitte, the output is
`output/quadratmeterpreise_zuschnitte_values.json`. It includes all seven
active categories and uses the current WAMI `Preis`, commercially rounded to a
whole number. Obsolete SKUs absent from current WAMI files are excluded.

Before replacing an existing consolidated JSON, the application archives it
under `backups/generated_prices/`.

All group source files must exist to build the complete JSON. Replacing one
category file preserves other categories through their current local files.
The reference JSONs define the schema; current WAWI files supply the prices.

## Client samples

Run `python generate_client_samples.py` to generate and verify all categories in
a fresh `output/client_samples_<timestamp>/` folder. Share its Excel/JSON files
with `REVIEW_REPORT.md`. Review source warnings before a live import. Local
verification does not replace the agency's Matrixify test import.

Run tests with `python -m unittest discover -s tests -v`.
