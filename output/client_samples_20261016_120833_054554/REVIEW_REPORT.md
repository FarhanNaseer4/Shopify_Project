# Client sample review

No Shopify upload was performed. All input/template hashes remained unchanged.

| Group | Category | Existing variants | New variants |
|---|---|---:|---:|
| Tafeln | Lochbleche | 562 | 19 |
| Tafeln | Streckmetall | 114 | 0 |
| Tafeln | Schweißgitter | 45 | 0 |
| Tafeln | Wellengitter | 35 | 1 |
| Zuschnitte | Lochblech | 156 | 0 |
| Zuschnitte | Präge | 6 | 0 |
| Zuschnitte | Glattblech | 14 | 0 |
| Zuschnitte | Schweißgitter | 27 | 0 |
| Zuschnitte | Wellengitter | 16 | 0 |
| Zuschnitte | Duett | 3 | 0 |
| Zuschnitte | PVC | 12 | 0 |

## Files and workflow

Each category update file has a Products sheet. Separate _NEW_ workbooks contain creation rows.
Review creation files before import. Refresh Shopify reference templates after successful creation imports.
Images, PDFs, Unit Price and inventory columns are omitted. Entirely empty columns are removed.
Existing products receive template-mapped technical fields and Tafeln prices; titles/options are preserved.
Complete JSON coverage: 776 Tafeln SKUs, 234 Zuschnitte SKUs.
No live products are deleted by these files.

## Source warnings requiring review

- SKU 1162: quantity prices increase at a higher tier; source values retained for review.
- SKU 14063: WAWI handle 'streckmetall-tafelware-62x20x7-5' differs; using Shopify reference 'streckmetall-tafelware-62x23x3'.
- SKU 15757: WAWI handle '#N/A' differs; using Shopify reference 'kunststoff-lochplatte-zuschnitt-qg-20-25-aus-pvc'.
- SKU 15763: WAWI handle '#N/A' differs; using Shopify reference 'kunststoff-lochplatte-zuschnitt-rv-6-14-aus-pvc'.
- SKU 15766: WAWI handle '#N/A' differs; using Shopify reference 'kunststoff-lochplatte-zuschnitt-rv-20-28-aus-pvc'.
- SKU 5061: quantity prices increase at a higher tier; source values retained for review.
- SKU 5920: WAWI handle 'lochblech-tafelware-quadratlochung-gerade-qg-8-12' differs; using Shopify reference 'lochblech-tafelware-quadratlochung-gerade-qg-10-12'.
- SKU 717: quantity prices increase at a higher tier; source values retained for review.
- SKU 806: WAWI handle 'lochblech-tafelware-rundlochung-gerade-rg-10-26' differs; using Shopify reference 'lochblech-tafelware-rundlochung-gerade-rg-10-25-98'.
- SKU 941: WAWI handle 'lochblech-tafelware-rundlochung-gerade-rg-10-21' differs; using Shopify reference 'lochblech-tafelware-rundlochung-gerade-rg-10-20-78'.

### Increasing price tiers (source values)

| SKU | Preis 1 | Preis 2 | Preis 4 | Preis 7 | Preis 10 |
|---|---:|---:|---:|---:|---:|
| 5061 | 845.376 | 595.476 | 511.224 | 549.78 | 339.864 |
| 1162 | 396.984 | 258.46799999999996 | 187.06799999999998 | 1510.8239999999998 | 128.51999999999998 |
| 717 | 292.74 | 295.12 | 246.32999999999998 | 226.1 | 217.76999999999998 |

## Checks passed

- Exact SKU coverage, no duplicates, and contiguous product rows in each category output.
- Products sheet name; no empty columns, images/PDFs, inventory quantity or Unit Price fields.
- Every Tafeln base price and both JSONs checked against WAWI using commercial rounding.
- Confirmed obsolete SKUs and Prägeblech Tafelware excluded.

Local checks passed. Agency review and a Matrixify test import are still required.
