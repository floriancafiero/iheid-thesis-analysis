# Hierarchical salience (empirical, no annotations)

This adds unsupervised per-entity document salience to the normalized entity hierarchy. First run `entity_hierarchy.py` locally on the raw JSONL. Then run:

```bash
pip install numpy scipy scikit-learn
python analysis/hierarchical_salience.py analysis/hierarchy_output/document_entities.csv --corpus entities_combined.jsonl.zip
```

The script accepts both committed hierarchy output (`direct`/`inherited`) and the detailed exploratory output (`mentions_direct`/`mentions_inherited`). Do not confuse direct country mentions with inherited mentions from its towns or regions. Each channel is modeled separately on the **same document universe**. Gamma-Poisson empirical Bayes accounts for corpus frequency, document length and overdispersion; among documents that mention an entity, one and two Gaussian regimes are compared via BIC. A high-frequency regime is used only if BIC improves by 10 or more and its rate is at least 1.5× that of the low regime. A probability of 90% is the main cutoff, with 80% and 95% sensitivity columns. Outcomes marked `not_separable` or `insufficient` are **not zero prevalence**: the split was not identified, so no salience prevalence can be reported. No claim is made that high frequency proves a thesis is *about* the entity.

**On the expanded counts:** city names can be bibliography publication locations, geopolitical or institutional references, not actual subject matter. Large direct/expanded differences (notably France/Paris, Switzerland/Geneva) must be treated as warning flags, not discoveries. The alias map is incomplete and historical entities/territories require special care. The source JSONL has no verified year or degree; results by decade are not possible before a metadata join. Institution alone is inferred from explicit document ID prefixes, with unmatched IDs separate.

Exploratory computed values for the user's supplied input (4,203 documents; from the richer local lexicon): China 157 direct vs 164 expanded high-salience documents; France 305 vs 678; Switzerland 135 vs 279; US 384 vs 388. These counts reflect separately fitted unsupervised models, not a strict monotonic inclusion relation. The user-facing output archive contains detailed CSVs and a figure; the compact GitHub dictionary and richer local dictionary are not yet identical.
