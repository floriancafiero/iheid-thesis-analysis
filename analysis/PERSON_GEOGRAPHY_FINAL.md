# Pipeline final – Géographie des thèses par les personnes (HEI / IUED / IHEID)

**Version arrêtée le 12 novembre 2026.** Objectif : atténuer le bruit bibliographique dans les courbes de pays avec un indicateur fondé sur les personnes nommées, sans devoir segmenter les bibliographies de l'OCR.

## Choix méthodologiques

1. **Corpus** : 1 730 doctorats corrigés (1928–2026), déduits du catalogue HEITH/« Thèse ». Masters exclus. Institut préservé (742 HEI, 23 IUED, 965 IHEID).
2. **NER** : toutes les formes PER/PERSON sont conservées dans la file, soit 36 669 formes, incluant les fautes NER/OCR. L'ancienne liste des 450 premières formes est abandonnée. Traitement par **lots techniques** `start`/`batch_size`, sans sélection scientifique d'un top 450. Les formes douteuses renvoyées par Wikidata sont automatiquement ignorées lorsque ce ne sont pas des humains, et les homonymes sont signalés comme ambigus.
3. **Identité Wikidata** : QID *humain* P31=Q5, appariement du nom/alias. Toute attribution ambiguë est écartée du calcul géographique. Les variantes reliées au même QID dans un même document sont cumulées.
4. **Filtre de bibliographie approximatif** : les personnes décrites dans Wikidata comme **sociologues, économistes, philosophes, politistes, chercheurs/universitaires, historiens, anthropologues, etc.** (P106 et un niveau de classes P279) sont exclues, **même si elles sont parfois étudiées**. `Michel Foucault`, `Karl Marx` et `Max Weber` sont exclus explicitement. En revanche, les artistes, diplomates, activistes, dirigeants, figures religieuses, etc. sont admissibles, pas uniquement les responsables politiques. Une double carrière incluant une occupation académique reste exclue par précaution. Le filtre ne prouve pas que les personnes restantes ne figurent pas en bibliographie.
5. **Pays** : d'abord la juridiction de la fonction P39→P1001/P17 si elle renvoie sans ambiguïté à un pays du référentiel ; sinon P27 comme **nationalité de repli** explicitement signalée. Aucune transformation automatique URSS→Russie, RDA→Allemagne ou Yougoslavie→États successeurs. Plusieurs pays / aucun pays / QID non normalisé = **inconnu**, non compté dans le signal national.
6. **Scores** : chaque couple (thèse, personne QID) est compté une fois dans le nombre de personnes distinctes, avec somme des occurrences de ses graphies. Par pays : `bio5` si ≥5 mentions cumulées ; `bio_strong` si `bio5` et soit ≥2 QID distincts, soit personne citée dans le titre. `direct5` = ≥5 mentions **directes** du pays dans les NER géographiques. `concordant` = `bio_strong` + `direct5`. Les pays déduits uniquement par nationalité sont conservés à part grâce à `country_basis`.
7. **Séries** : pour chaque institut séparément, proportion de thèses signalées par pays, fenêtre centrée 9 ans HEI, 5 ans IHEID, 15 ans IUED (cette dernière peu fiable avec seulement 23 thèses). Les années 2020–2026 ne constituent pas une décennie complète. Pas de raccord artificiel à la fusion de 2008.

## Lancer Wikidata depuis GitHub Actions

`Actions → Wikidata - identifier les personnes NER → Run workflow`

- `start = 0`, `batch_size = 100`, `delay = 0.7` pour une première passe ; puis `start = 100`, `200`, etc. Les lots sont un **contrôle de charge réseau**, pas une sélection du corpus. Les résultats CSV sont téléchargés dans les Artifacts.
- Le workflow produit **deux CSV** : `candidate_qids.csv` (identités candidates et homonymies) et `person_country_links.csv` (provenance, filtres académiques, statut géographique). Ils ne doivent pas être confondus.
- Faire passer les lots couvrant la file entière si l'on veut une couverture exhaustive. Vérifier la proportion de `network_error`, les collisions et les pays non mappés. Enrichir les correspondances douteuses par contrôle manuel, sans forcer automatiquement.

## Recalculer localement les pays

Installer `pandas matplotlib numpy requests` pour le graphique et l'enrichissement. Télécharger les Artifacts correspondant aux lots Wikidata dans un répertoire. Puis :

```bash
python analysis/aggregate_person_countries.py \
  --ner doctoral_ner_recovered.jsonl.zip \
  --metadata doctoral_metadata_recovered.csv \
  --country-ner document_entity_counts.csv \
  --people results/wikidata/batch*/person_country_links.csv \
  --verified analysis/verified_actor_registry.csv \
  --out results/person_geography
```

Fichiers de sortie : `person_doc_counts.csv`, `doc_country_scores.csv`, `rolling_country_by_institute.csv`, `surface_conflicts.csv`, `report.json`, deux heatmaps. Le registre de 61 QID vérifiés permet de **tester sans API**, mais le graphique ainsi obtenu est un pilote, pas le résultat final exhaustif.

## Limites assumées

- Les classes d'occupation dans Wikidata sont incomplètes, parfois multiples. Le filtre peut écarter un véritable sujet (Marx) et conserver une référence (un dirigeant cité dans un article). C'est l'approximation demandée, pas une mesure de bibliographie.
- P27 ne mesure ni la sphère d'influence d'une personne, ni nécessairement le sujet de la thèse ; conserver les deux niveaux de confiance et publier les limites.
- La vérification des entités OCR/NER n'est pas corrigée sur le texte source ; toutes les décisions sont réexécutables depuis les registres, scores et logs.
- **Important** : le GitHub Action interroge Wikidata mais ne peut recalculer les séries doctorales tant que les fichiers de NER et métadonnées corrigés ne sont pas fournis à l'environnement d'exécution. Ne pas prétendre que les séries finales ont été recalculées après chaque action Wikidata.