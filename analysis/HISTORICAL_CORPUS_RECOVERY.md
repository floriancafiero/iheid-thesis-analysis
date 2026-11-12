# Corrected doctoral population — 1928–2026

The original scanned ALTO catalog has an explicit **`Contenu`** classification: `Thèse / HEITH <number>` versus `Diplôme / HEIDI <number>`. The secondary `thesis_metadata.csv` incorrectly designated all pre-1990 NER documents `Master/Other` because the older `Directeur(s)` metadata field is blank.

Of 762 dated 1927–1989 NER works, **444 are identified as theses**, 314 as diplomas, and four lack a definitive class. Separately, 22 post-1990 `HEITH` works were mislabeled `Master/Other`. This raises the research corpus from 1,264 to **1,730 doctoral texts**, dated **1928–2026**.

No master's diplomas are included, and the four uncertain historical works remain excluded. Unlike our previous statement, doctorate series do **not** begin in 1990. The original catalog field overrides the erroneous derived `Master/Other` tag only where the source is explicit.

The full result archive (delivered in chat) includes a streaming XLSX extractor, source-linked audit, corrected filtered JSONL, decade counts, recalculated entity salience and plots. To reproduce this commit's script, first extract the source workbook into a CSV containing `Nom livrable` and `Contenu`, then pass that CSV with the original `thesis_metadata.csv` and `entities_combined.jsonl.zip`.

The models **were re-fitted** on the corrected 1,730 doctoral texts: 240 fits, 88 BIC-supported high-concentration splits. Beware small early decades (1920s n=2), incomplete 2020s, historical name aliases, and uneven institution/disciplines. Strong mention concentration is not equivalent to manually verified thesis topics.

Historical volumes: 1920s 2, 1930s 41, 1940s 24, 1950s 50, 1960s 76, 1970s 104, 1980s 147, 1990s 145, 2000s 290, 2010s 549, 2020–2026 302.
