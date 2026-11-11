# Document-level salience analysis (IHEID)

The file `entities_combined.jsonl.zip` contains entity counts and processed word counts **per document**, but does **not** provide document years or degree types. It is not included in the repository: supply it locally.

Run: `python analysis/document_salience.py entities_combined.jsonl.zip`

For historical comparisons: `python analysis/document_salience.py entities_combined.jsonl.zip --metadata metadata.csv`, where the CSV has columns `doc_id,year,institution,degree`. This is essential before interpreting any chronological pattern or distinguishing PhD from MA.

Outputs are `analysis/output/document_entities.csv` and `analysis/output/summary.csv`. The measures are (1) document count and word volume, (2) significant document prevalence, using **at least 5 mentions AND at least 2 per 10,000 words** as an exploratory threshold, (3) mentions per 100,000 words, and (4) log2 specificity against the overall corpus. The cutoff is configurable; don't treat it as a validated topic classifier. Counts are aggregated across conservative French/English aliases. Ambiguous OCR strings are excluded; the country and organization dictionaries are deliberately editable and non-exhaustive. Institution is inferred only for explicit HEI/IUED/IHEID ID prefixes, otherwise listed as `Unmapped`.

**Important:** this is exploratory NER, not a topic model. Some mentions originate in citations, bibliographies, or OCR errors. For historical interpretation inspect both prevalence and intensity, and compare degree types separately (IUED has relatively few doctorates). Do not interpret a peak in raw mentions without checking document volume and coverage.
