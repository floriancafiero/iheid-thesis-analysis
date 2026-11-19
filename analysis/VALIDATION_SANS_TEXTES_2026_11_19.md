# Les thèses HEI/IUED/IHEID : reprise avec les données déjà disponibles

**Audit et résultats complémentaires — 19 novembre 2026.**

## Résumé exécutif

Aucune archive supplémentaire n'est requise pour cette analyse. Le jeu de données corrigé contient **1 730** enregistrements doctoraux de 1928 à 2026, sans masters ; **1 621** dans la version conservatrice qui écarte **109 doublons très probables**, les 48 autres collisions restant non arbitrées. Les données NER sont limitées à **50 graphies par type et par thèse** : l'inventaire Wikidata exhaustif est exhaustif **à l'intérieur de ce plafond**, non de l'intégralité des textes.

Une comparaison indépendante avec les titres de thèses apporte un contrôle positif : sur **190 couples titre–pays**, **184 (96,84 %)** disposent également de cinq mentions NER directes ; sur **75 couples titre–organisation**, **73 (97,33 %)**. Les titres constituent un *contrôle positif partiel*, non un estimateur de précision/rappel général. Ces proportions ne démontrent pas que les mentions des autres thèses sont thématiques : les bibliographies ne sont pas isolées et les en-têtes répétés peuvent contribuer aux décomptes.

**Découverte importante** : au moins **5 thèses** nomment explicitement une personne que le filtre des professions Wikidata a exclue comme académique, notamment Frédéric Bastiat, F. D. Roosevelt, Arthur Koestler, François Mitterrand et Hans Morgenthau. Les occupations P106 ne doivent plus servir à un rejet automatique des identités.

**Évolution récente** : la part de documents classés anglophones augmente de **18,43 % à 30,67 %** entre les doctorats IHEID des années 2010 et de 2020–2026 ; la médiane des mots effectivement traités descend de **125 021 à 92 236**. Après ajustement exploratoire simultané sur la langue et la longueur traitée, les baisses de mention de l'ONU, des États-Unis et de la France s'atténuent sensiblement. Une « redistribution » de leurs objets de recherche ne peut pas être démontrée à ce stade.

## A. Contrôle positif par les titres

Lexiques exacts conservateurs, multilingues, séparant explicitement SDN/ONU, CEE/CE/UE et URSS/Russie. Les adjectifs, les acronymes courts ambigus et les rapprochements flous sont généralement exclus. Les formes négatives ne signifient pas qu'une thèse n'étudie pas le sujet.

| Catégorie | Thèses dont le titre nomme au moins une entité du lexique | Couples titre–entité | Couples avec NER directe ≥5 | Taux conditionnel |
|---|---:|---:|---:|---:|
| Pays | 169 | 190 | 184 | 96,84 % |
| Organisations | 72 | 75 | 73 | 97,33 % |

**Exceptions conservées (8 couples)** : titres nommant des entités avec moins de 5 mentions NER, dont *The World Health Organization* (HEI, 1957 : OMS=0), *African participation at the World Trade Organization* (IHEID, 2012 : OMC=0), et *Israel between France and the United States, 1962–1968* (IHEID, 2015 : France=0, Israël=0). La non-détection peut tenir à la troncature top 50, à la segmentation NER, au dictionnaire et à l'OCR ; on ne peut pas discriminer ces causes sans contexte textuel.

**Exemples historiques** : HEI, années 1930 : SDN dans 4 titres (25/41 thèses avec ≥5 mentions directes) ; HEI, années 1950 : ONU dans 4 titres (29/50 avec ≥5 mentions) ; IHEID 2010–2019 : ONU dans 4 titres (160/483 avec ≥5 mentions) et 2020–2026 : ONU dans 1 titre (68/300 avec ≥5 mentions). Les petits effectifs en titre ne permettent pas d'affirmer un changement thématique à eux seuls.

## B. Les cinq exclusions P106 falsifiées par le titre

| Personne | Année | Institut | QID | Ancien statut |
|---|---:|---|---|---|
| Frédéric Bastiat | 1959 | HEI | `Q13515` | excluded_academic |
| Franklin Delano Roosevelt | 1989 | HEI | `Q8007` | excluded_academic |
| Arthur Koestler | 1992 | HEI | `Q78494` | excluded_academic |
| François Mitterrand | 2002 | HEI | `Q2038` | excluded_academic |
| Hans Morgenthau | 2008 | IHEID | `Q77161` | excluded_academic |

Ces cinq correspondances NER et noms complets dans les titres démontrent que la règle d'exclusion académique est trop agressive ; elles ne prouvent pas que le QID de chaque occurrence hors titre est correct. Les personnes de carrières multiples doivent rester candidates ; les pays de nationalité P27 sont séparés de l'objet de la thèse. N'attribuer aucun pays « étudié » à une thèse sur Morgenthau à partir de sa citoyenneté.

## C. Triangulation pays des personnes et pays nommés dans les titres

| Canal de liaison personne–pays | Même pays explicitement nommé dans le titre | Autre pays explicitement nommé | Aucun pays explicite du lexique |
|---|---:|---:|---:|
| Registre vérifié | 59 | 34 | 293 |
| Fonction officielle | 34 | 14 | 144 |
| Nationalité (repli) | 31 | 31 | 252 |

Ce contrôle porte sur les **894 couples thèse–personne** disponibles : les catégories par canal sont disjointes. Une différence entre le pays attribué à une personnalité et le pays du titre **n'est pas** une erreur prouvée : diplomatie bilatérale, comparaison et références théoriques peuvent expliquer la divergence. Les 62 cas avec titre de pays et lien par nationalité se partagent également entre concordance (31) et autre pays (31), ce qui rappelle que P27 n'est pas un étiquetage thématique.

## D. Comparaison IHEID 2010–2019 / 2020–2026

**Mesure** : pourcentage des thèses avec cinq mentions NER directes de l'entité. **Population** : 483 doctorats (2010–2019) contre 300 (2020–2026) dans le corpus dédoublonné. Le seuil de cinq mentions est descriptif, non validé comme classifier de sujet principal. Les modèles statistiques ajustent la langue NER (`fr`, `en`, `de`) et le logarithme du nombre de mots traités. Les écarts ajustés proviennent d'une standardisation marginale sur les covariables de la cohorte 2010–2019 (logistique binomiale avec erreurs-types robustes HC1).

| Entité | 2010–2019 | 2020–2026 | Écart brut (pts) | Écart ajusté (pts) | OR ajusté (IC 95 %) |
|---|---:|---:|---:|---:|---:|
| United States | 53.0% | 45.3% | -7.7 | -4.1 | 0.84 (0.62–1.14) |
| France | 37.7% | 29.7% | -8.0 | -3.5 | 0.85 (0.61–1.18) |
| China | 20.9% | 23.0% | +2.1 | -0.4 | 0.97 (0.68–1.40) |
| India | 21.9% | 21.7% | -0.3 | -1.8 | 0.89 (0.62–1.29) |
| ONU | 33.1% | 22.7% | -10.5 | -2.8 | 0.86 (0.60–1.23) |
| Construction européenne (strictement CEE→CE→UE) | 13.0% | 6.7% | -6.4 | -5.6 | 0.52 (0.30–0.90) |

**Lecture** : les baisses des États-Unis, de la France et de l'ONU diminuent nettement après ajustement et leurs intervalles d'OR incluent 1 ; on ne peut donc pas les présenter comme une preuve solide de déplacement des sujets. La légère hausse apparente de la Chine disparaît après ajustement. La construction européenne et la Banque mondiale conservent des écarts négatifs plus prononcés, mais les tests sont exploratoires, multipliés, et exposés au biais de mesure et aux transformations disciplinaires.

**Sensibilité** : avec les 109 doublons probables conservés, les principales conclusions restent du même ordre (par exemple États-Unis −4,81 points ajustés et ONU −3,53, contre respectivement −4,12 et −2,82 après dédoublonnage). Les chiffres exacts sont dans les deux tableaux de régression exportés.

La standardisation **sur la langue seule** est présentée séparément dans `language_standardized_changes.csv`. Elle ne corrige pas le biais de longueur : l'ONU passe de −10,46 points bruts à −9,88 points après contrôle de langue seul, mais seulement −2,82 points dans l'ajustement langue + mots traités.

### Sensibilité du choix de seuil

La tendance brute ne dépend pas exclusivement du seuil de cinq mentions. Dans les doctorats IHEID, le signal États-Unis au seuil ≥10 passe de **40,2 % à 30,3 %**, celui de la France de **31,3 % à 19,3 %**, tandis que la Chine reste stable (**15,9 % à 15,3 %**). En imposant simultanément au moins cinq mentions **et** au moins deux mentions pour 10 000 mots, les États-Unis passent de **23,2 % à 16,7 %**, la France de **11,8 % à 8,3 %**, et la Chine de **10,4 % à 11,0 %**. La direction descriptive est assez stable, mais ces seuils ne neutralisent ni le top 50, ni les différences de langue, de section bibliographique ou de discipline. Tableau complet : `threshold_sensitivity.csv`.

## E. Ce que les données permettent et ne permettent pas

**Établi sur les sources disponibles** : identification exhaustive des 36 669 graphies NER (dans le plafond existant), traçabilité des 109 exclusions de doublons probables, contrôle positif de 265 titres–entités, 5 exclusions académiques incompatibles avec la lecture des titres, analyses descriptives et contrôles de composition linguistique et longueur.

**Non établi** : précision générale du matching QID, taux de mention dans le corps de texte versus bibliographie, évolution de l'ensemble des personnes étudiées (plafond top 50), mesure complète de la diversité géographique, correspondance entre la juridiction d'une fonction P39 et le pays sujet de thèse. Le modèle de langue est lui-même issu d'une détection approximative ; `words_processed` n'est pas une longueur physique garantie du manuscrit. Les contrôles ne neutralisent pas la variation disciplinaire. Les années 2020–2026 forment une période incomplète et l'IUED (23 doctorats) est trop petit pour des comparaisons fines.

## F. Réplicabilité sans autre donnée

Les nouveaux scripts utilisent **uniquement** les fichiers récupérés et les sorties antérieures du projet : `doctoral_metadata_recovered.csv`, `doctoral_ner_recovered.jsonl.zip`, `thesis_country_evidence.csv`, `duplicate_audit.csv`, `iheid_systematic_ner_2026.zip`, `candidate_qids.csv`, `person_country_links.csv`, `person_doc_links.csv`.

- `title_anchor_validation.py` : titres de pays/organisations et 265 couples titre–entité ; deux modes (1 730 ou 1 621).
- `title_person_checks.py` : identités humaines dans les titres, y compris professions académiques ; 5 couples après déduplication par QID.
- `person_title_geo_audit.py` : comparaison des pays des personnes avec ceux explicitement mentionnés dans les titres.
- `language_mix_sensitivity.py` : proportions corrigées des changements de langue, tableaux par langue.
- `adjusted_document_trends.py` : régression exploratoire selon cohorte, langue et mots traités ; comparaison avec/sans doublons probables.
- `test_title_anchor_analysis.py` : 5 tests ciblant les frontières de titres, la séparation des États historiques, le mapping des organisations et les faux positifs.

Tous les tableaux sont exportés sans jugement manuel inventé. L'analyse met le plus loin possible les données disponibles à contribution **sans prétendre remplacer une validation au niveau des passages**.