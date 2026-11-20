# Disciplines des doctorats HEI, IUED et IHEID, 1928–2026

**Statut : analyse exploratoire, 20 novembre 2026.** Corpus dédoublonné : **1 621** doctorats (742 HEI, 23 IUED, 856 IHEID). Les 109 doublons écartés sont des doublons probables du corpus de 1 730 notices.

## Identification de la discipline

Les **856 doctorats IHEID de 2008–2026** ont été rapprochés à l'identique (titre normalisé, année et notice) du catalogue doctoral 2008–2026. Leur discipline provient des champs `Specialisation-1` et `Dpt-1`, non d'une inférence :
- DODR/DR → **Droit**
- DOEC, DOECD, EC → **Économie**
- DOHP, DOHPD, HP → **Histoire internationale**
- DOSP, SP → **Science politique / relations internationales**
- DOANT → **Anthropologie et sociologie**
- DODEV → **Études du développement**, programme interdisciplinaire.
- Les codes génériques DORI et DOEI sont désambiguïsés par le code de département.

Les **765 titres HEI/IUED** ont été classés par un modèle de texte entraîné sur les 856 titres et sous-titres contemporains de discipline connue (TF-IDF mots/caractères et régression logistique). Validation croisée stratifiée cinq plis : **73,0 % de bonnes classifications**, macro-F1 **0,669** ; pour le sous-ensemble de scores ≥0,60 : **88,4 %** de bonnes classifications sur **62,4 %** des titres contemporains. Un contrôle distinct de marqueurs textuels explicites complète le modèle (par exemple « droit », « macroeconomics », « ethnography »). Les titres anciens sont **hors distribution temporelle** et la précision estimée sur les thèses récentes ne s'y transfère pas automatiquement.

Deux séries sont conservées : **probable** (seuil 0,40 et marqueurs) ; **prudente** (seuil 0,60, marqueurs explicites, sinon « indéterminée »). Dans la version prudente, **318 doctorats historiques HEI sur 742 (42,9 %) restent indéterminés**.

## Série longue, version prudente

Pourcentages par période parmi **tous** les doctorats de la période, indéterminés compris :

| Période | n | Droit | Histoire | Économie | Science politique / RI | Anthropologie / sociologie | Développement | Indéterminés |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HEI 1928–1945 | 51 | 29,4 | 15,7 | 2,0 | 5,9 | 0,0 | 0,0 | 47,1 |
| HEI 1946–1960 | 71 | 29,6 | 18,3 | 1,4 | 2,8 | 0,0 | 1,4 | 46,5 |
| HEI 1961–1977 | 156 | 23,1 | 26,3 | 2,6 | 2,6 | 0,6 | 1,3 | 43,6 |
| HEI 1978–1990 | 177 | 19,2 | 13,6 | 13,0 | 7,3 | 0,6 | 1,1 | 45,2 |
| HEI 1991–2007 | 287 | 24,4 | 14,3 | 13,2 | 7,0 | 0,7 | 1,0 | 39,4 |
| IUED 1999–2008 | 23 | 4,3 | 4,3 | 0,0 | 0,0 | 0,0 | 34,8 | 56,5 |
| IHEID 2008–2011 | 164 | 29,9 | 18,3 | 19,5 | 14,0 | 0,0 | 18,3 | 0,0 |
| IHEID 2012–2016 | 255 | 30,6 | 14,9 | 17,6 | 16,1 | 3,1 | 17,6 | 0,0 |
| IHEID 2017–2020 | 171 | 26,3 | 13,5 | 24,6 | 19,9 | 15,8 | 0,0 | 0,0 |
| IHEID 2021–2026 | 266 | 26,7 | 15,8 | 21,4 | 19,9 | 16,2 | 0,0 | 0,0 |

## Interprétation et réserves

1. Les titres historiques font apparaître un noyau de **droit international** et d'**histoire/diplomatie**, tandis que l'**économie** devient beaucoup plus identifiable à partir des années 1978–1990. La proportion élevée d'indéterminés interdit de traiter les pourcentages historiques comme des taux disciplinaires administratifs établis.
2. Dans les données **officielles** IHEID postérieures à 2008, le droit conserve environ un quart à un tiers des doctorats, l'économie environ un cinquième, tandis que les programmes en sciences politiques et en anthropologie/sociologie prennent plus de place.
3. La disparition apparente de « Études du développement » après 2016 est **une évolution de nomenclature/programme**, non la preuve d'une disparition des thèmes du développement ; elle ne doit pas être interprétée comme un changement thématique.
4. La série IUED n'inclut que **23 doctorats**, très loin de ses autres productions diplômantes ; ne pas extrapoler son profil à toute son histoire.
5. Ne pas prolonger la série HEI inférée par la série IHEID officiellement codée sans représenter la **rupture de méthode**.

Un classeur téléchargeable a été produit dans la conversation, avec les **1 621 titres et leurs étiquettes**, les variantes probable/prudente, les scores, les alternatives et les tableaux de périodes. Le paquet reproductible contient les trois scripts `iheid_discipline_analysis.py`, `iheid_discipline_refine.py` et `iheid_discipline_reporting.py`, plus les entrées précédemment récupérées.
