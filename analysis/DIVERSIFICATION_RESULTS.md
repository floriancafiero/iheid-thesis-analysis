# Doctoral NER diversification (1991–2026)

The population is 1,264 dated doctoral texts (all masters and pre-1927 items excluded; earliest matched PhD is 1991). The 2020s are incomplete. IUED has 23 doctoral texts. Input must be the **doctoral-only refit** salience scores, not the full-corpus scores.

Only direct entity mentions are used to avoid bibliography place contamination. Only the **25 country entities and 9 organizations** for which two NER-frequency regimes were BIC-supported enter diversity calculations. Main cutoff: >= 90% posterior probability of high salience; 80% and 95% are sensitivity checks.

Two indicators: (1) *rarefied richness*, the expected number of distinct high-salience entities in a sample of 100 doctorates from that decade, calculated exactly using hypergeometric non-detection probabilities; (2) inverse Simpson effective diversity, 1 / sum(p_i^2), where p_i is the share of strong *document/entity pairs* attributed to entity i. One thesis can contribute multiple pairs.

| Decade | Countries per 100 PhDs | Effective countries | Organizations per 100 PhDs | Effective organizations |
|---|---:|---:|---:|---:|
| 1990s | 22.09 | 11.27 | 4.81 | 4.28 |
| 2000s | 19.30 | 11.77 | 7.12 | 5.76 |
| 2010s | 17.74 | 14.81 | 7.41 | 6.70 |
| 2020–2026 | 16.02 | 12.41 | 6.70 | 5.94 |

**Interpretation:** geographic *breadth* at fixed sample size decreases, while *evenness* increases through the 2010s. Institutional diversity grows to the 2010s, then declines in the incomplete 2020s. A two-sided exploratory document-label permutation of the effective-diversity difference (2010s vs 1990s; 3,000 draws) yields p ≈ 0.18 for countries and p ≈ 0.09 for organizations, **not conventionally significant**. Institution and period are confounded, making the test descriptive only. Bootstrap percentiles are diagnostic intervals, not calibrated confidence intervals; finite-sample resampling can show downward bias.

Do not interpret 'strong NER concentration' as verified dissertation subject matter. Entities without an identified high-frequency regime are excluded, *not* absent from the corpus. HEI/IHEID periods and disciplines differ; the sample cannot support claims about 1927–1989.

Reproduce: `python analysis/compute_diversification.py --metadata analysis/doctoral_output/doctoral_metadata_1927plus.csv --scores analysis/hierarchy_salience/document_scores.csv --diagnostics analysis/hierarchy_salience/diagnostics.csv`.
