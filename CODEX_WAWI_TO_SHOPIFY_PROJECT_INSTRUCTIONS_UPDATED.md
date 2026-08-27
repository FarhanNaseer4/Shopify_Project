# WAWI → Shopify / Matrixify Converter
## Updated Complete Development Instructions for Codex

### 1. Project Objective

Build a reusable local Python application that converts WAWI product export files into Shopify/Matrixify-compatible Excel import files.

The client has two broader product groups:

- Zuschnitte
- Tafeln

Each broader group contains multiple product categories with slightly different WAWI structures and Shopify output rules.

The user will manually select:
1. The broader group (`Zuschnitte` or `Tafeln`)
2. The exact category
3. The WAWI `.xlsx` input file

The program must then:
1. Read the selected WAWI Excel file.
2. Load the correct Shopify template workbook for the selected broader group.
3. Read the category-specific Shopify template sheet from that workbook.
4. Read the `WAWI-Match` and `Legende (Befüllhilfe)` sheets from the same template workbook.
5. Apply the correct category-specific mapping and transformation rules.
6. Group WAWI rows into Shopify products and variants.
7. Generate Shopify Handle and Title values.
8. Map `Artikel-Nr.` to Variant SKU.
9. Populate fixed Shopify/Matrixify technical values from the legend.
10. Populate source-driven fields from WAWI.
11. Transform Material, Stärke, Format, Farbe and other option values into the required Shopify option handles.
12. Handle pricing and quantity-tier logic.
13. Generate a Shopify/Matrixify-ready `.xlsx` file.
14. Save the output in a local output folder.
15. Produce useful validation, logging and processing statistics.

This is a local data transformation application.

It does NOT need:
- website scraping
- Shopify API
- Google Drive API
- Google Sheets API
- database
- server
- browser automation

---

## 2. Technology

Use:

- Python 3.11+ / 3.12 compatible
- pandas
- openpyxl
- pathlib
- json from Python standard library where required
- logging
- argparse and/or a simple interactive CLI

The application must work on:

- macOS
- Windows

Avoid OS-specific hardcoded paths.

Use `pathlib.Path` wherever possible.

---

# 3. Actual Project Folder Structure

The files are already organized locally into separate folders.

Expected project structure:

```text
wawi_shopify_converter/
│
├── main.py
├── requirements.txt
├── README.md
│
├── Templates/
│   ├── <template workbook containing "Tafeln" in filename>.xlsx
│   └── <template workbook containing "Zuschnitte" in filename>.xlsx
│
├── WAMI_Zuschnitte/
│   ├── category source files...
│
├── WAMI_Tafeln/
│   ├── category source files...
│
├── output/
│
├── config/
│   ├── categories.py
│   ├── mappings.py
│   ├── transformations.py
│   └── constants.py
│
├── src/
│   ├── workbook_reader.py
│   ├── category_processor.py
│   ├── grouping.py
│   ├── transformer.py
│   ├── pricing.py
│   ├── shopify_builder.py
│   ├── validator.py
│   └── exporter.py
│
├── logs/
│
└── tests/
```

Important:

- All source/reference files are `.xlsx`.
- CSV input support is NOT required for this project unless added later.
- Do not modify original WAWI or template workbooks.
- Generated files must go into `output/`.

The existing folder names may be kept exactly as supplied.

---

# 4. Template Workbooks

There are TWO Shopify reference/template workbooks inside the `Templates` folder.

One workbook contains `Tafeln` in its filename.

The other workbook contains `Zuschnitte` in its filename.

Codex must identify them by filename rather than relying on a hardcoded full filename.

For example:

```python
def find_template(group: str, templates_dir: Path) -> Path:
    # group = "Tafeln" or "Zuschnitte"
    # find a .xlsx filename containing that word case-insensitively
```

There should be exactly one matching workbook for each group.

If zero or multiple matches are found, fail with a clear message.

---

# 5. Important Template Workbook Structure

Each template workbook is self-contained.

DO NOT expect separate standalone files for:
- legend
- WAWI matching

They are already included as sheets inside each template workbook.

For example, the Tafeln template workbook contains category sheets such as:

```text
Lochbleche
Präge
Streckmetall
Schweißgitter
Wellengitter
...
WAWI-Match
Legende (Befüllhilfe)
```

The Zuschnitte workbook similarly contains its own category sheets plus its own:
- `WAWI-Match`
- `Legende (Befüllhilfe)`

Therefore the template workbook is the central source of truth for:
1. expected Shopify columns
2. expected category output examples
3. WAWI → Shopify matching
4. legend/fixed technical values

---

# 6. Reference Priority

When deriving business rules, use this priority:

1. Category-specific completed/example sheet in the correct template workbook
2. `Legende (Befüllhilfe)` sheet in that workbook
3. `WAWI-Match` sheet in that workbook
4. Source WAWI file
5. Written project instructions

Do not invent mapping behavior when it can be determined from the template workbook.

If examples conflict with an older written note, prefer the workbook examples.

---

# 7. Initial Codex Analysis — Mandatory

Before writing the converter, inspect the complete project folder.

Codex's FIRST task must be analysis only.

It must inspect:

```text
Templates/
WAMI_Zuschnitte/
WAMI_Tafeln/
```

For both template workbooks report:

- exact filename
- all sheet names
- sheet dimensions
- which sheets are product/category examples
- location/name of `WAWI-Match`
- location/name of `Legende (Befüllhilfe)`

For all WAWI source workbooks report:

- filename
- workbook sheet names
- used sheet
- row count
- column count
- exact headers
- likely category
- likely broader group

Also report:

- total Zuschnitte categories
- total Tafeln categories
- unique WAWI schemas
- differences between categories
- matching template sheet for each WAWI category
- uncertain category/template matches

Do NOT begin full implementation until this analysis is complete.

---

# 8. Product Groups

There are two broad groups:

```text
Zuschnitte
Tafeln
```

The client previously indicated:

- Zuschnitte: 7 categories
- Tafeln: 4 categories

However, Codex must derive the final actual category list from the folders and template sheets instead of relying only on this count.

The application must not assume there are only five categories.

---

# 9. Manual Category Selection

The category should NOT be automatically chosen as the primary workflow.

The user will manually select it.

Recommended CLI:

```text
Select product group:

1. Zuschnitte
2. Tafeln
```

Then:

```text
Select category:

1. Lochbleche
2. Präge
3. Streckmetall
...
```

Then select the corresponding WAWI `.xlsx` file.

The script may perform automatic schema detection afterward only as a validation check.

Example:

```text
Selected category: Lochbleche
Selected input: WAMI_Tafeln/lochblech.xlsx

Schema check passed.
```

If the file clearly does not match:

```text
The selected input file does not match the expected Lochbleche structure.
```

---

# 10. Source File Discovery

For `Zuschnitte`, allow the user to select files only from:

```text
WAMI_Zuschnitte/
```

For `Tafeln`, allow selection only from:

```text
WAMI_Tafeln/
```

Do not mix both directories.

The conversion engine should also accept a direct file path programmatically for testing.

---

# 11. Template Sheet Selection

Once the user selects a category:

- select the appropriate group template workbook
- select the category sheet corresponding to that category

Do not recreate the Shopify schema manually.

Use the category template sheet to derive:

- destination columns
- exact ordering
- sample Shopify values
- blank/nonblank patterns
- option fields
- technical columns
- category-specific metafields

The system should use configuration mapping where category display names differ slightly from filenames or sheet names.

Example:

```python
CATEGORY_CONFIG = {
    "tafel_lochblech": {
        "group": "Tafeln",
        "template_sheet": "Lochbleche",
    },
    "tafel_praege": {
        "group": "Tafeln",
        "template_sheet": "Präge",
    },
}
```

---

# 12. WAWI-Match Sheet

Each template workbook contains a `WAWI-Match` sheet.

Use it to understand:

```text
WAWI source field
        ↓
Shopify/Matrixify destination field
```

Do not require a separate `wawi_matching.csv`.

Build mapping configuration based on this sheet.

If the match sheet uses visual formatting or category-dependent references, inspect those carefully using openpyxl.

---

# 13. Legend Sheet

Each template workbook contains:

```text
Legende (Befüllhilfe)
```

Use it to determine:

- fixed technical values
- column meaning
- required constants
- values such as `MERGE`
- fields that should remain blank
- calculation notes
- other Matrixify requirements

Do not require a separate `legend.csv`.

Centralize resolved constants in code after analysis.

Example:

```python
FIXED_VALUES = {
    "Command": "MERGE",
    ...
}
```

But values must come from the workbook, not assumptions.

---

# 14. WAWI Source Format

All WAWI source files are Excel `.xlsx` files.

Use:

```python
pandas.read_excel(...)
```

and/or `openpyxl` where cell styles, formulas, or raw workbook structure matter.

Important:
- preserve SKU values as strings
- avoid accidental `.0` suffixes
- preserve URLs
- preserve German text
- normalize NaN to empty values where appropriate

No CSV input handling is required in version 1.

---

# 15. Known WAWI Structures

Examples already identified:

## Tafeln — Lochblech style

```text
Def-Lochung
Lochgröße und -abstand
Material
Stärke
Format
Bild
Datenblatt
Lagerplatz
Untertitel
Preis 1
Preis 2
Preis 3
Preis 4
Preis 5
Preis 6
Preis 7
Preis 8
Preis 9
Preis 10
Versand
Artikel-Nr
Material-Gruppe
DIN-Bezeichnung (alt)
DIN-Bezeichnung (neu)
SpezifischesGewicht
Ao, gelochte Fläche
Gewicht pro Tafel
DIN
Daten 9
Daten 10
Hinweis
```

## Tafeln — Streckmetall style

```text
Def-Lochung
Maschenlänge und -breite
Material
Stärke
Format
Bild
Datenblatt
Lagerplatz
Untertitel
Preis 1
...
Preis 10
Versand
Artikel-Nr
Material-Gruppe
DIN-Bezeichnung (alt)
DIN-Bezeichnung (neu)
SpezifischesGewicht
Ao, ungelochte Fläche
Gewicht pro Tafel
DIN
Daten 9
Daten 10
Hinweis
```

## Tafeln — Schweißgitter / mesh style

```text
Def-Lochung
Maschenweite
Material
Drahtstärke
Format
Bild
Datenblatt
Lagerplatz
Untertitel
Preis 1
...
Preis 10
Versand
Artikel-Nr
Material-Gruppe
DIN-Bezeichnung (alt)
DIN-Bezeichnung (neu)
SpezifischesGewicht
Ao, ungelochte Fläche
Gewicht pro Tafel
DIN
Daten 9
Daten 10
Hinweis
```

## Tafeln — Wellengitter example

May only contain selected price columns:

```text
Preis 1
Preis 2
Preis 4
Preis 7
Preis 10
```

Do not require all ten price columns.

## Zuschnitte example

```text
Def-Lochung
Lochgröße und -abstand
Material
Stärke
Bild
Datenblatt
Preis
Lagerplatz
Untertitel
Artikel-Nr
Material-Gruppe
DIN-Bezeichnung (alt)
DIN-Bezeichnung (neu)
SpezifischesGewicht
Ao, gelochte Fläche
Gewicht pro m²
DIN
Daten 9
Daten 10
Hinweis
```

Typical Zuschnitte differences:
- no `Format`
- one `Preis`
- `Gewicht pro m²` instead of `Gewicht pro Tafel`

Actual schemas must be derived from all project files.

---

# 16. Normalized Internal Schema

Because column names vary, convert source rows into a common internal structure.

Example:

```python
{
    "group": "Tafeln",
    "category": "Lochbleche",
    "definition": "...",
    "dimension": "...",
    "material": "...",
    "thickness": "...",
    "format": "...",
    "color": "...",
    "image": "...",
    "datasheet": "...",
    "storage_location": "...",
    "subtitle": "...",
    "sku": "...",
    "material_group": "...",
    "din_old": "...",
    "din_new": "...",
    "specific_weight": "...",
    "area_value": "...",
    "weight": "...",
    "din": "...",
    "data_9": "...",
    "data_10": "...",
    "note": "...",
    "price": ...,
    "price_tiers": {...},
}
```

Category configuration maps real WAWI headers into these normalized concepts.

---

# 17. Column Aliases

Known equivalent concepts include:

```text
Lochgröße und -abstand
Maschenlänge und -breite
Maschenweite
```

These can all represent the category-specific product dimension/size field.

Likewise:

```text
Stärke
Drahtstärke
```

or:

```text
Ao, gelochte Fläche
Ao, ungelochte Fläche
```

or:

```text
Gewicht pro Tafel
Gewicht pro m²
```

Do not spread raw aliases throughout business logic.

Use configuration.

---

# 18. Grouping Products and Variants

Each WAWI row represents a variant.

Rows belonging to the same product must be grouped into one Shopify product.

Known rule from client:

```text
Def-Lochung + Größe
```

The actual Größe-equivalent is category dependent.

Examples:
- Lochgröße und -abstand
- Maschenlänge und -breite
- Maschenweite
- another category-specific dimensional field

The exact grouping behavior must be confirmed against the category example sheet.

Implement per-category grouping config.

Example:

```python
"group_by": ["definition", "dimension"]
```

Do not group by SKU.

SKU identifies a variant.

---

# 19. Variant SKU

Map:

```text
Artikel-Nr.
→ Variant SKU
```

This is the stable unique key.

Preserve it exactly.

Do not:
- slugify it
- change punctuation
- convert to integer
- add `.0`

Read and write SKU as text.

Also use SKU when comparing old/new Shopify structures if needed by the examples.

---

# 20. Handle Generation

Generate new Shopify Handle values based on:

```text
Def-Lochung + category-specific dimension/size
```

Use the category template examples to infer exact formatting.

Known transformations may involve:
- lowercase
- spaces → hyphens
- German character handling
- punctuation cleanup
- decimal normalization

But do not assume generic slugification is enough.

Build and test exact rules.

---

# 21. Product Title Generation

Generate Title from:

```text
Def-Lochung + dimension
```

Use exact example formatting.

Create separate logic:

```python
generate_title(...)
generate_handle(...)
```

Do not derive one by reversing the other.

---

# 22. Variant Options

Known Shopify option dimensions include:

```text
Material
Stärke
Format
```

For some products such as PVC:

```text
Farbe
Material
Stärke
```

The exact option structure must be derived from each template category sheet.

The script needs to write the correct option handle/value.

The `Linked To` field must remain as specified in the category template/legend.

Do not generate unrelated Shopify metafields unless the template requires them.

---

# 23. Known Value Transformations

Examples supplied by client:

```text
Aluminium (ohne Folie)
→ aluminium-ohne-folie
```

```text
1,50 mm
→ 1-5
```

```text
Mittelformat (1250 x 2500 mm)
→ mittelformat
```

```text
weiß
→ weiss
```

Derive the full rule set from the examples.

Use transformation helpers and lookup maps.

Example:

```python
MATERIAL_HANDLE_MAP = {}
FORMAT_HANDLE_MAP = {}
COLOR_HANDLE_MAP = {}
```

Avoid repeated long `if/elif` chains.

---

# 24. German Character Handling

Keep display values and normalized Shopify handles separate.

For example:

```python
raw_display_value = "weiß"
option_handle = "weiss"
```

Do not globally transliterate every text field.

Descriptive/metafield fields may need original German characters.

---

# 25. Product-Level vs Variant-Level Values

The category example sheets show how product rows and variant rows should look.

Determine:
- which fields are only populated on the first row of a product
- which fields repeat on every variant
- which fields remain blank on following variant rows

Do not blindly repeat all product-level values.

Use completed category examples as truth.

---

# 26. Fixed Technical Fields

Grey/technical Matrixify columns must be filled according to `Legende (Befüllhilfe)` and the example sheet.

Examples may include:

```text
Command = MERGE
Variant Command = MERGE
```

There may be other values.

Do not hardcode values before reading the workbook.

---

# 27. Source-Driven / Green Fields

Source-driven fields are populated from WAWI according to:
- WAWI-Match
- category template
- example rows

Possible values include:

```text
Artikel-Nr.
Material
Stärke
Format
Lagerplatz
Untertitel
Material-Gruppe
DIN-Bezeichnung (alt)
DIN-Bezeichnung (neu)
SpezifischesGewicht
Ao...
Gewicht...
DIN
Daten 9
Daten 10
Hinweis
Bild
Preis...
```

---

# 28. Metafields

Category templates may include category-specific metafields.

Known or possible concepts:
- Material-Gruppe
- DIN-Bezeichnung
- spezifisches Gewicht
- gelochte/ungelochte Fläche
- Gewicht pro Tafel
- Gewicht pro m²
- DIN
- Daten 9
- Daten 10
- Hinweis
- Geprägte Fläche
- Freie Fläche
- Toleranzen
- Drahtüberstände

Inspect actual template columns.

Do not assume identical metafields across categories.

---

# 29. Images

`Bild` contains product image data/URL.

Use category example behavior to determine where image values are written.

Do not download images.

Do not upload images to Shopify.

Output the image reference/URL required by the template.

---

# 30. Datenblatt

Do not build PDF download/upload logic.

If the category output template directly expects a data-sheet URL, preserve/map it according to the example.

Otherwise leave it out as shown in the reference workbook.

---

# 31. Pricing — Tafeln

Tafeln can use:

```text
Preis 1
Preis 2
...
Preis 10
```

Known intent:
- `Preis 1` is base/variant price in some structures
- later price fields represent quantity tiers
- quantity-tier values may need JSON

However, exact behavior must be derived from:
- category example
- legend
- WAWI-Match

Some categories do not contain all tiers.

Example:

```text
Preis 1
Preis 2
Preis 4
Preis 7
Preis 10
```

Only use columns that exist and contain values.

Do not fail because Preis 3, 5, 6, etc. are absent.

---

# 32. Pricing — Zuschnitte

Zuschnitte may use only:

```text
Preis
```

Treat it with its own pricing mode.

Do not reuse tier pricing automatically.

---

# 33. Quantity Tier JSON

If the Shopify template requires quantity-tier JSON:

- derive the exact JSON schema from the template workbook
- do not invent a format
- isolate JSON creation in one function

Example architecture:

```python
build_quantity_price_json(...)
```

If no complete reference exists, clearly flag it during analysis.

---

# 34. Template Workbook Reading

Use `openpyxl.load_workbook()` for template analysis because:
- multiple sheets must be inspected
- styles/colors may be meaningful
- formulas may exist
- legends/matches are workbook-native

Use pandas selectively for table-like content.

Do not destroy workbook structure during analysis.

For output, create a new workbook/dataframe following the category sheet column structure.

Do not overwrite the template workbook.

---

# 35. Preserve Exact Output Column Order

Output must use exact Shopify/Matrixify column order from the selected category template sheet.

Do not:
- alphabetize columns
- append internal fields
- rename columns
- drop required blank columns

Create output using template headers.

---

# 36. Output Format

Version 1 output should be `.xlsx`.

The client confirmed Excel is fine, and all project/reference files are Excel.

No CSV output is required.

Suggested naming:

```text
shopify_Tafeln_Lochbleche_20260815_103500.xlsx
```

or:

```text
shopify_Zuschnitte_<category>_20260815_103500.xlsx
```

Include:
- group
- category
- timestamp

Never silently overwrite an existing output.

---

# 37. Output Folder

Create:

```text
output/
```

if it does not exist.

Every run creates one output workbook there.

Do not write into:
- Templates
- WAMI_Zuschnitte
- WAMI_Tafeln

---

# 38. User Workflow

Target workflow:

```text
1. Export/download the relevant WAWI Excel file.
2. Place it in:
   WAMI_Zuschnitte/
   OR
   WAMI_Tafeln/
3. Run the converter.
4. Select broader group.
5. Select category.
6. Select source .xlsx file.
7. Script validates selected file structure.
8. Script reads correct group template workbook.
9. Script loads the selected category sheet, WAWI-Match and legend.
10. Script processes product/variant data.
11. Script validates the generated output.
12. Output .xlsx is saved into output/.
13. Client imports/tests it in Shopify/Matrixify.
```

No source code changes should be needed by the client.

---

# 39. Processing Summary

Show a clean summary at completion.

Example:

```text
Processing complete.

Group: Tafeln
Category: Lochbleche
Input file: Lochbleche.xlsx
Input rows: 2,842
Products created: 411
Variants created: 2,842
Duplicate SKU warnings: 0
Missing required values: 2
Warnings: 3

Output:
output/shopify_Tafeln_Lochbleche_20260815_103500.xlsx
```

---

# 40. Logging

Create logs in:

```text
logs/
```

Example:

```text
logs/run_20260815_103500.log
```

Log:
- selected group
- selected category
- source file
- template workbook
- template sheet
- WAWI row count
- generated products
- generated variants
- missing columns
- duplicate SKUs
- transformation warnings
- errors
- output file

---

# 41. Validation

Before conversion:

### Source validation
Check expected category columns.

### Template validation
Check category template sheet exists.

Check:
- `WAWI-Match` exists
- `Legende (Befüllhilfe)` exists

### SKU validation
- SKU not unexpectedly blank
- duplicate SKU detection
- exact text preservation

### Product validation
- no blank Handle
- no blank Title
- grouping consistency

### Output validation
- exact template headers
- exact column order
- no internal helper columns
- correct row count pattern

### Pricing validation
- numeric values handled safely
- missing price tiers accepted where valid
- no invalid JSON if JSON is required

---

# 42. Error Handling

Examples:

### Wrong source file for category

```text
Selected category: Streckmetall

The chosen workbook does not match the expected structure.

Missing required columns:
- Maschenlänge und -breite
- Artikel-Nr.
```

### Missing template

```text
No template workbook containing 'Tafeln' was found in Templates/.
```

### Missing category sheet

```text
Template sheet 'Lochbleche' is missing.
```

### Empty workbook

Stop cleanly.

Do not create output if critical validation fails.

---

# 43. Category Configuration

Use a centralized configuration.

Example:

```python
CATEGORY_CONFIG = {
    "tafel_lochbleche": {
        "group": "Tafeln",
        "template_sheet": "Lochbleche",
        "definition_column": "Def-Lochung",
        "dimension_column": "Lochgröße und -abstand",
        "material_column": "Material",
        "thickness_column": "Stärke",
        "format_column": "Format",
        "sku_column": "Artikel-Nr.",
        "price_mode": "tiers",
    },
}
```

Example Zuschnitte config:

```python
{
    "group": "Zuschnitte",
    "format_column": None,
    "price_mode": "single",
    "weight_column": "Gewicht pro m²",
}
```

Do not duplicate complete processors for each category.

---

# 44. Code Quality

Requirements:
- modular
- type hints
- docstrings where useful
- no giant `main.py`
- no duplicated business logic
- configurable category mappings
- no absolute paths
- no credentials
- no network dependency
- clean error messages
- deterministic transformations

---

# 45. Tests

Create unit tests for:
- handle generation
- title generation
- German-character option normalization
- decimal/thickness normalization
- material handle mapping
- format mapping
- grouping
- SKU preservation
- pricing tier parsing
- missing tiers
- template header extraction

Create integration tests from supplied sample data.

Compare generated values against category example sheets.

---

# 46. Reference-Driven Comparison

Before marking a category complete:

1. Read the WAWI source sample.
2. Read matching category template sheet.
3. Convert source.
4. Compare generated Handle.
5. Compare Title.
6. Compare SKU.
7. Compare option values.
8. Compare technical fields.
9. Compare mapped metafields.
10. Compare image fields.
11. Compare pricing.
12. Compare quantity-tier JSON.
13. Compare blank/nonblank behavior.
14. Compare output column order.

Any difference must be explained.

---

# 47. Revision-Friendly Architecture

The client expects multiple Shopify import test/revision cycles.

Therefore:
- centralize mappings
- centralize fixed values
- centralize transformations
- centralize option handle rules
- isolate pricing logic
- isolate category differences in config

Do not hardwire rules inside random processing functions.

---

# 48. Mac Compatibility

The final application must be simple for a non-technical Mac user.

Provide a `README.md` containing:

```bash
cd path/to/wawi_shopify_converter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Explain:
- how to install Python if needed
- how to open Terminal
- how to navigate to project folder
- how to install dependencies
- where to put WAWI files
- how to run script
- how to choose group/category/file
- where output is generated

---

# 49. Optional Mac Launcher

If straightforward, create:

```text
run_mac.command
```

It can:
- activate `.venv`
- run `main.py`

But do not make the entire system depend on the launcher.

---

# 50. Core Conversion Function

Keep CLI separate from business logic.

Core API should look similar to:

```python
convert_wawi_to_shopify(
    group="Tafeln",
    category="Lochbleche",
    input_file=Path(...),
    templates_dir=Path("Templates"),
    output_dir=Path("output"),
)
```

This allows a GUI later without rewriting conversion code.

---

# 51. Implementation Phases

## Phase 1 — Analyze folders and workbooks

Inspect:
- Templates
- WAMI_Zuschnitte
- WAMI_Tafeln

Create an analysis report.

## Phase 2 — Resolve category/template mapping

Map every WAWI category to:
- group
- template workbook
- template sheet
- source schema

## Phase 3 — Implement common engine

Build:
- workbook reader
- template parser
- legend reader
- match reader
- normalized record mapper
- grouping
- validator
- exporter
- logger

## Phase 4 — Implement first representative category

Prefer Lochbleche/Tafeln if it is the largest/most complete example.

Compare generated output carefully.

## Phase 5 — Add remaining categories

Reuse common code and add configuration/differences only.

## Phase 6 — Pricing and JSON

Validate against template examples.

## Phase 7 — Regression testing

Run every supplied category sample.

## Phase 8 — README / Mac setup

Finish user instructions.

---

# 52. Do Not Guess

If something cannot be confidently inferred:

- identify the category
- source field
- destination field
- example values observed
- reason it is ambiguous

Do not silently invent a transformation.

---

# 53. Business Rules Summary

```text
Input:
.xlsx WAWI workbooks only

Source folders:
WAMI_Zuschnitte/
WAMI_Tafeln/

Templates:
Templates/

Template identification:
filename contains "Zuschnitte" or "Tafeln"

Template workbook contains:
- all category Shopify example/template sheets
- WAWI-Match
- Legende (Befüllhilfe)

User selection:
manual group + category + source workbook

Processing:
one category per run

Product grouping:
Def-Lochung + category-specific dimension/size

Variant key:
Artikel-Nr. → Variant SKU

Handle/Title:
generated from examples

Options:
category-specific

Fixed values:
from workbook legend/template

Source mappings:
from workbook WAWI-Match and category examples

Tafeln pricing:
category-specific tier logic

Zuschnitte pricing:
single-price logic where applicable

Output:
.xlsx only

Output folder:
output/

Network/API:
none

Supported OS:
macOS + Windows
```

---

# 54. Definition of Done

Project is complete when:

1. Both product groups are supported.
2. All supplied category structures are supported.
3. User manually selects group and category.
4. User selects an `.xlsx` source file from correct local folder.
5. Correct template workbook is selected automatically by filename.
6. Correct category sheet is loaded.
7. `WAWI-Match` is read from the template workbook.
8. `Legende (Befüllhilfe)` is read from the template workbook.
9. Products/variants are grouped correctly.
10. SKU mapping is correct.
11. Handle generation matches examples.
12. Title generation matches examples.
13. Option transformations match examples.
14. Fixed Matrixify fields match reference.
15. WAWI fields map correctly.
16. Pricing matches category examples.
17. Output column order matches template.
18. Output `.xlsx` imports successfully during Shopify/Matrixify testing after agreed revisions.
19. Original files remain unchanged.
20. Mac setup/usage is documented.
21. Processing logs and validation summaries are available.

---

# 55. FIRST ACTION FOR CODEX

Before changing or creating conversion code:

Inspect the current folders:

```text
Templates/
WAMI_Zuschnitte/
WAMI_Tafeln/
```

Then produce a structured analysis containing:

1. Exact two template workbook filenames.
2. Every sheet in each template.
3. Which sheets are category examples.
4. Confirmation of `WAWI-Match`.
5. Confirmation of `Legende (Befüllhilfe)`.
6. Every WAWI source workbook.
7. Every source workbook header list.
8. Every source row count.
9. Identified product group.
10. Identified category.
11. Matching template sheet.
12. Unique schemas.
13. Differences between schemas.
14. Product grouping rule per category.
15. Handle examples.
16. Title examples.
17. Shopify option mappings.
18. Known transformations.
19. Fixed values.
20. Source → destination mappings.
21. Pricing rules.
22. Quantity-tier JSON format if present.
23. Any ambiguities.

After the analysis, propose the implementation plan before coding the full conversion engine.

Do not alter any original workbook.
