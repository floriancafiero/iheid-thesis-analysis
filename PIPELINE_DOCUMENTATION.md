# IHEID Thesis NER Analysis Pipeline Documentation

## Overview

This pipeline extracts and analyzes Named Entities (locations, organizations, persons) from IHEID thesis documents spanning 1928-2026.

```
Source Documents → Text Extraction → NER → Entity Normalization → Visualizations
```

## Data Sources

### 1. ALTO XML Documents (1928-2007)
- **Source**: Digitized thesis archive (OCR'd)
- **Count**: 3,392 documents
- **Format**: ALTO XML → Plain text with page markers
- **Location**: `ALTO_text/*.txt`

### 2. PDF Documents (2008-2026)
- **Source**: `iheid_phd_theses_2008-2026.zip`
- **Count**: 861 PhD theses
- **Format**: PDF → Plain text with page markers
- **Location**: `PDF_text_full/*.txt`

## Processing Statistics

| Metric | ALTO | PDF | Combined |
|--------|------|-----|----------|
| Documents | 3,392 | 861 | 4,253 |
| PhD theses | 453 | 861 | 1,314 |
| Master theses | 2,939 | 0 | 2,939 |
| Avg pages (PhD) | 364 | ~300 | - |
| Avg words (PhD) | 141,073 | ~100,000 | - |

## Pipeline Steps

### Step 1: Text Extraction

**ALTO Documents:**
```bash
python extract_alto_text.py
```
- Parses ALTO XML files
- Extracts text from `<String CONTENT="..."/>` elements
- Preserves page markers: `--- Page 0001 ---`

**PDF Documents:**
```bash
python extract_pdf_text.py "iheid_phd_theses_2008-2026.zip" PDF_text_full --max-pages 500 --workers 4
```
- Extracts PDFs one-by-one from zip (memory efficient)
- Uses pypdf for text extraction
- Preserves page markers: `--- Page 1 ---`

### Step 2: Language Detection

Simple keyword-based detection:

| Language | Keywords |
|----------|----------|
| French | le, la, les, de, du, des, et, en, un, une... |
| English | the, of, and, to, in, is, for, that, with... |
| German | der, die, das, und, ist, von, mit, für... |

### Step 3: NER Extraction

```bash
python extract_ner.py <input_dir> <output.jsonl> --words 100000 --workers 6
```

**spaCy Models:**
- English: `en_core_web_sm`
- French: `fr_core_news_sm`
- German: `de_core_news_sm`

**Entity Types:**
- `LOC`: Locations (countries, cities, regions)
- `ORG`: Organizations
- `PER`/`PERSON`: Person names
- `MISC`: Miscellaneous

**Output Format (JSONL):**
```json
{
  "doc_id": "HEI_000310--000004_410301",
  "language": "fr",
  "words_processed": 141073,
  "total_entities": 8234,
  "entities_by_type": {
    "LOC": {"france": 245, "geneva": 123, ...},
    "ORG": {"united nations": 89, ...},
    "PER": {"max weber": 12, ...}
  }
}
```

### Step 4: Entity Normalization

**Country Normalization** (`analyze_entities.py`):
Merges multilingual variants into canonical English names:

| Canonical | Variants |
|-----------|----------|
| USA | united states, états-unis, vereinigte staaten, america... |
| Germany | allemagne, deutschland, german... |
| France | français, frankreich... |
| Switzerland | suisse, schweiz... |

**International Organizations:**

| Canonical | Variants |
|-----------|----------|
| United Nations | onu, nations unies, vereinte nationen... |
| WTO | omc, world trade organization... |
| IMF | fmi, international monetary fund... |
| WHO | oms, world health organization... |

### Step 5: Metadata Consolidation

```bash
python consolidate_all_data.py
```

**Sources:**
1. `IHEID_LOT_1_MD_FILTRE_SUR_THESES.xlsx` - ALTO metadata
2. `phd_2008-2026_metatda.xlsx` - New PhD metadata

**PhD Identification:**
- ALTO: Has `Directeur(s)` field = PhD thesis
- New PDFs: All are PhD (from dedicated PhD collection)

**Output:** `output/data/thesis_metadata.csv`

| Column | Description |
|--------|-------------|
| doc_id | Unique document identifier |
| author | Author name |
| title | Thesis title |
| year | Publication year (1928-2026) |
| thesis_type | "PhD" or "Master/Other" |
| institution | HEI, IUED, or IHEID |

### Step 6: Visualization Generation

```bash
python regenerate_visualizations.py
```

**Normalization:**
All visualizations use **per 100,000 words** normalization:
```
normalized_count = raw_count / words_in_year * 100000
```

This ensures fair comparison across years with different document volumes.

**Output Files:**
- `continents_interactive.html`
- `countries_interactive.html`
- `ios_interactive.html` (International Organizations)
- `ngos_interactive.html`
- `persons_interactive.html`
- `thesis_timeline.html`

**Features:**
- Smoothing options: Raw, 3-year, 5-year, 7-year, 10-year
- Per 100k words normalization
- Top N entity filtering
- Interactive Plotly charts

## Data Structure

```
output/
├── data/
│   ├── thesis_metadata.csv      # 11,091 records
│   └── texts/                   # Full text files
│       ├── HEI_*.txt           # ALTO documents
│       ├── IUED_*.txt
│       ├── IHEID_*.txt
│       └── *.txt               # PDF documents (numeric IDs)
├── *.html                       # Interactive visualizations
└── PIPELINE_DOCUMENTATION.md    # This file

entities_combined.jsonl          # Merged NER results (all documents)
```

## Key Scripts

| Script | Purpose |
|--------|---------|
| `extract_alto_text.py` | Extract text from ALTO XML |
| `extract_pdf_text.py` | Extract text from PDFs in zip |
| `extract_ner.py` | Run spaCy NER on text files |
| `analyze_entities.py` | Entity normalization functions |
| `consolidate_all_data.py` | Merge metadata sources |
| `merge_entities.py` | Combine NER JSONL files |
| `regenerate_visualizations.py` | Generate Plotly charts |

## Reproducibility

To regenerate all outputs:

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Extract PDF texts (if not done)
python extract_pdf_text.py "iheid_phd_theses_2008-2026.zip" PDF_text_full --max-pages 500 --workers 4

# 3. Run NER on all texts
python extract_ner.py ALTO_text/ entities_alto.jsonl --words 1000000 --workers 6
python extract_ner.py PDF_text_full/ entities_pdf.jsonl --words 1000000 --workers 6

# 4. Merge NER results
python merge_entities.py entities_alto.jsonl entities_pdf.jsonl -o entities_combined.jsonl

# 5. Consolidate metadata
python consolidate_all_data.py

# 6. Regenerate visualizations
python regenerate_visualizations.py
```

## Known Limitations

1. **OCR Quality**: ALTO text depends on original scan quality
2. **PDF Extraction**: Some PDFs are encrypted or image-only
3. **Language Detection**: Simple keyword-based, may misclassify multilingual docs
4. **Entity Boundaries**: spaCy may include articles (e.g., "l'URSS")
5. **Historical Entities**: USSR/Soviet entities mapped to Russia

## Version History

- **v1.0** (Sept 2024): Initial ALTO-only pipeline
- **v2.0** (Nov 2024): Added PDF support, normalization fix, extended to 2026

---

*Last updated: November 2024*
