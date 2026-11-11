# Doctorates only — strict historical analysis population

The default historical analysis population is **PhD only**, **year >= 1927**, and **present in the NER JSONL**. All masters and other works are excluded, including IUED masters. IUED **doctoral** works remain eligible. Unknown/invalid years are excluded, not imputed. The filter depends on the metadata's actual `thesis_type` field, not the institution or file name. Original source files are not modified.

Run:
```bash
python analysis/filter_doctorates.py thesis_metadata.csv entities_combined.jsonl.zip --hierarchy analysis/hierarchy_output/document_entities.csv --out analysis/doctoral_output
```

The hierarchy CSV can also be the richer local `document_entities_hierarchical.csv`. The script emits filtered doctoral metadata, the actual filtered NER JSONL, a filtered hierarchy CSV, excluded-ID audit, decade counts and a JSON report. Always run salience models on the **filtered JSONL** rather than merely filtering previously fitted all-document scores: the fitted reference distribution depends on the population.

Checked on the user's uploads: 4,203 unique NER documents; **1,264 included PhDs** (HEI 276; IUED 23; IHEID 965); **2,939 non-PhDs excluded**; **zero pre-1927 PhDs** and zero undated PhDs in the NER subset. The broader metadata catalog contains doctoral notices without matching NER text and two undated supplementary catalogue rows sharing document IDs with dated main records. These are not additional NER documents. The counts here refer only to the 4,203-document NER set.

This excludes IUED masters from analysis and does not imply that the 23 IUED PhDs represent IUED's complete research activity.
