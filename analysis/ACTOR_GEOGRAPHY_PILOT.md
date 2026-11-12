# IHEID — pilote de géographie par les personnalités politiques (NER × Wikidata)

## Corpus et objectif

1 730 thèses (HEI, IUED, IHEID), 1928–2026, sans masters. Le NER de personnes (`PER` + `PERSON`) est très bruité et les noms de bibliographies sont nombreux. L'objectif est **un signal complémentaire, positif et vérifiable**, et non un modèle complet de pertinence géographique.

## Validation des personnes

`verified_actor_registry.csv` contient **34 personnes aux identités Wikidata vérifiées** et des surfaces NER acceptées explicitement, avec QID, poste et **État/autorité correspondant à l'exercice d'une fonction politique**, plutôt que nationalité ou lieu de naissance. Ex. Kissinger → États-Unis (et non Allemagne), Jiang Zemin → Chine ; les universitaires n'exerçant pas de fonction politique sont exclus de ce registre. Une fonction transnationale comme la présidence de la Commission européenne n'est pas attribuée automatiquement à la nationalité du titulaire. L'URSS et la RDA sont distinguées de la Russie et de l'Allemagne réunifiée ; pour la RDA, il n'existe pas de comparaison directe avec un pays dans l'inventaire géographique présent.

**Ne pas confondre exhaustivité des 34 vérifications et exhaustivité des figures politiques.** Les alias sont conservateurs, en général des noms complets. Le réseau n'était pas accessible à l'environnement de calcul pour faire tourner à grande échelle l'API Wikidata. Les URL Wikidata vérifiables sont dans le registre. La généralisation automatisée peut réutiliser `wikidata_link.py` du prototype antérieur, sous réserve d'une vraie désambiguïsation des personnes et juridictions ; ne jamais affecter un pays à partir du seul P27.

## Indicateurs par document/pays

- `country_ner_ge5` : au moins cinq occurrences directes harmonisées du pays ; exclut les villes et les régions héritées.
- `actor_ge5` : au moins cinq mentions NER cumulées de personnalités dont les rôles sont identifiés dans le registre et associés à l'État ou autorité.
- `actor_2distinct_ge5` : comme ci-dessus, avec au moins deux personnes Wikidata différentes.
- `concordant_ge5` : les deux premières conditions simultanément.
- `actors_ge5_country_less5` : signal biographique sans cinq mentions directes du pays ; ce n'est **pas** une preuve que la thèse porte sur le pays.

## Résultats exploratoires

- 34 personnes, 8 205 occurrences reconnues, 181 thèses avec au moins une de ces personnes, 222 couples thèse/pays avec au moins une personne.
- Sur 203 couples thèse/juridiction avec >=5 mentions de ces personnes, 2 concernent la RDA sans mesure géographique directement comparable. Sur les **201 cas comparables**, 180 (**89,6 %**) ont aussi >=5 mentions directes du pays.
- **51** couples thèse/pays comportent >=5 mentions cumulées réparties sur >=2 acteurs distincts : tous ont >=5 mentions géographiques directes (51/51). Ces chiffres dépendent du registre sélectionné et ne mesurent pas la précision d'un classifieur à grande échelle.
- Sur les 21 couples personnes >=5 / pays <5, certaines thèses portent sur un espace tiers ou traitent un personnage extérieur : par ex. Lloyd George dans un travail sur le Kurdistan, Mao dans un travail sur Marx et Lénine. Dans d'autres cas, le signal complète effectivement le NER géographique : Patrice Lumumba dans *Les grandes puissances et le Congo*.

Ce modèle pilote **confirme généralement** un pays déjà repéré, mais n'autorise pas à éliminer les pays lorsque le signal biographique manque : 34 acteurs ne couvrent qu'une petite partie des responsables politiques mondiaux, et une thèse sur l'économie ou la société peut ne citer aucun dirigeant.

## Reproduction

```bash
python actor_geography.py \
  --zip ../iheid_catalog_recovery/doctoral_ner_recovered.jsonl.zip \
  --metadata ../iheid_catalog_recovery/doctoral_metadata_recovered.csv \
  --countries ../iheid_revision/systematic/document_entity_counts.csv \
  --registry verified_actor_registry.csv --out results
python plot_actor_concordance.py
```

Fichiers : `results/doc_actor_country.csv`, `results/country_comparison.csv`, `results/actor_totals.csv`, `results/matched_ner_surfaces.csv`, `results/unlinked_top100.csv`, `results/report.json`, `actor_country_concordance.png`.

Les vérifications de sensibilité (personnes >=3/5/10, au moins deux personnalités, rôle local vs national) et l'extension du dictionnaire par le service Wikidata sont des améliorations futures. Aucune inférence sur l'intégralité des thèses n'est justifiée à ce stade.