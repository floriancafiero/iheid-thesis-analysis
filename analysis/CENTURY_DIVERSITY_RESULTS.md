# A century of doctoral research: change in attention, not just expansion

**Dataset:** 1,730 dated doctoral texts, 1928–2026, based on the corrected original `HEITH` vs `HEIDI` catalog classification; no masters. The 1920s have only two doctoral works, so the comparisons group years into four epochs: 1928–1959 (117), 1960–1989 (327), 1990–2009 (435), 2010–2026 (851). The last epoch is incomplete.

Main measurement uses document-level statistically *strong direct mentions* of countries/organizations, not place names inherited from cities. The model was refit over 1,730 PhDs and only BIC-supported high-rate entities are eligible (31 countries, 13 organizations). Other entities are not scored as absent. See `analysis/century_diversity.py` for exact rarefaction and inverse-Simpson calculations.

| Epoch | Countries / 100 PhDs | Effective countries | Organizations / 100 PhDs | Effective organizations |
|---|---:|---:|---:|---:|
| 1928–1959 | 20.45 | 9.95 | 2.85 | 2.00 |
| 1960–1989 | 21.56 | 12.37 | 8.35 | 6.29 |
| 1990–2009 | 24.16 | 13.80 | 9.49 | 8.72 |
| 2010–2026 | 20.39 | 18.56 | 9.24 | 8.42 |

The historical story: declining concentration on France (23.1% high country salience in the first era to 4.2% in last) and US (19.7% to 3.9%); China's corresponding values 2.6% to 4.6%. The geographic *balance* rises strongly, whereas standardized *breadth* does not rise monotonically. The organization distribution becomes much more diverse, with UN high-rate mentions (7.7% early vs 1.5% late), EEC more salient 1960–1989 (4.0%), WTO and World Bank in 1990–2009 (4.4% and 4.1%), and Human Rights Watch and UNHCR salient since 2010 (4.9% and 2.4%). The absence of League of Nations or EU from the high-salience plots reflects non-separable statistical models, **not** an absence of research on them.

Exploratory permutation comparison of early and late effective diversities gave p≈0.003 for countries and p<0.001 for organizations, but the samples differ dramatically in size, institutional provenance, period and discipline. Also, many modern organizations did not exist in the founding decades. The tests are descriptive and must not be used to claim an identified historical causal break. Neither can this corpus establish a specific impact of the 2008 HEI–IUED merger (few IUED doctorates).

**Interpretive conclusion:** not a continuous addition of more countries studied, but a more balanced allocation of scholarly attention among them, combined with a more differentiated institutional landscape. Subject concentration is inferred from NER and unvalidated by human document labeling; bibliography/OCR and alias coverage are remaining limitations.

The full calculated CSVs, figures and a French 2-page narrative accompany the conversation's downloadable analysis archive.
