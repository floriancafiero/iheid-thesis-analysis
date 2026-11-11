# Re-estimated salience on doctorate-only NER subset

The original JSONL was filtered to 1,264 dated PhDs (HEI 276, IUED 23, IHEID 965); no masters, no pre-1927 works. **The earliest PhD in the NER subset is from 1990.** Therefore no claims about 1927–1989 can be grounded in these doctoral curves.

The complete models were refit on the filtered doctoral corpus (not transferred from models fit on all 4,203 documents): 240 country/organization × direct/expanded models, with 67 statistically separable. A gamma-Poisson overdispersion correction and empirical-Bayes log rates precede one-vs-two mixture BIC comparison; threshold posterior probability >=0.90. 0.80 and 0.95 columns are retained for sensitivity. Unsupported splits are **NA / not separable**, not zero prevalence.

Counts of PhDs in the NER corpus by decade:
- 1990s: HEI 121, IUED 2 (total 123)
- 2000s: HEI 155, IUED 21, IHEID 114 (total 290)
- 2010s: IHEID 549
- 2020–2026: IHEID 302 (incomplete decade)

Selected **direct-mention** salience prevalences in 1990s / 2000s / 2010s / 2020–2026, in percent:
- United States: 20.3 / 13.4 / 5.8 / 3.6
- France: 8.9 / 9.0 / 5.3 / 2.3
- China: 8.1 / 4.8 / 3.1 / 5.3
- India: 3.2 / 2.8 / 2.4 / 5.6
- Brazil: 3.2 / 5.5 / 2.7 / 4.6
- Russia: 4.9 / 3.8 / 3.6 / 0.7
- WTO: 0.8 / 6.2 / 4.4 / 2.6

The direct US model has 107 high-concentration doctorates; China 57; France 73; World Bank 36; IMF 32. Expanded US (with cities/regions) has **no supported split**, so no expanded-US prevalence is reported; expanded France is strongly affected by Paris and possible bibliography noise. The UN direct model also has no supported two-regime split. The presence of historical state names (e.g. USSR/Russia) should be treated separately.

**Interpretation warnings:** comparisons are descriptive, not causal, and strongly confounded by institution and shifting corpus composition. IUED PhD n=23 is too small for definitive comparisons. A high-rate regime is *not* equivalent to a thesis demonstrably being about a country or organization. Very common geographical locations in references are a known source of false positive salience.

Run the accompanying `analysis/doctoral_trends.py` against the refitted doctoral scores and filtered metadata. The scripts do not require the large raw JSONL or derived outputs to be committed to the repository; those should be supplied locally.
