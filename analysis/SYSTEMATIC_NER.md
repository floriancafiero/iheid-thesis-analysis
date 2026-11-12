# Harmonisation systématique des entités NER (1928–2026)

**Pipeline :** `analysis/systematic_ner.py`, dictionnaire versionné `analysis/systematic_ner_dictionaries.json`. Le corpus de départ est le JSONL des **1 730 doctorats** rétabli à partir des codes de catalogue HEITH/HEIDI.

Reproduction :

```bash
pip install rapidfuzz
python analysis/systematic_ner.py --ner doctoral_ner_recovered.jsonl.zip --metadata doctoral_metadata_recovered.csv --dictionary analysis/systematic_ner_dictionaries.json --output analysis/systematic_output
```

**Chaque couple (type NER, graphie brute) est systématiquement inventorié**, même si son identité reste inconnue. Les statuts sont `canonical`, `child_place`, `ambiguous`, `candidate`, `unresolved` et `noisy`. Une clé `normalized_surface_id` unifie les formes orthographiques, mais **n'est pas une preuve d'identité référentielle**. Les correspondances floues ne sont jamais comptées automatiquement. Les attributs contrôlés comprennent pays, ville/région héritée, organisation et appartenance à une famille.

La liste d'alias n'est **pas** un système universel de désambiguïsation de toutes les personnes, lieux, œuvres et organismes du corpus. L'inventaire exhaustif des 225 173 couples forme/type et la file de révision des candidats figurent dans l'archive fournie au cours de cette conversation.

**Nomenclature temporelle :**
- SDN vs ONU : entités distinctes, variétés FR/EN/DE rassemblées dans chacune.
- CEE / CE / UE : trois entités historiques distinctes, plus une famille analytique de continuité. `EC`, `EU` et `UN` ambiguës ne sont pas fusionnées par défaut.
- GATT / OMC, CSCE / OSCE : identités distinctes et familles comparables.
- Mentions de villes (Shanghai → Chine, Vaud → Suisse) conservées dans un canal `inherited`, jamais amalgamées aux mentions directes.
- Anachronismes flagrants (par exemple CEE attribuée avant 1958) isolés dans `date_anomalies.csv` et exclus des séries principales. Une référence rétrospective à une institution disparue n'est pas un anachronisme.
- Les courbes annuelles sont calculées **par institut** ; fenêtres mobiles de 5, 9 et 15 ans, sans faire passer une courbe indifférenciée par la fusion de 2008.

**Audit exécuté :** 1 730 documents, 7 784 767 occurrences NER toutes catégories, 225 173 couples type/graphie ; 10 validations de conservation, chronologie et séparation institutionnelle réussies. L'identification institutionnelle des entités mentionnées reste partielle : les formes ambiguës et non résolues sont explicitement exportées et jamais interprétées comme des absences.

Les statistiques normalisées peuvent changer par rapport aux figures précédentes, qui utilisaient un dictionnaire incomplet et quelques acronymes ambigus. Une présence de cinq mentions n'est pas une mesure garantie du sujet principal d'une thèse.

**Exports (archive liée au chat) :** `all_surface_inventory.csv`, `review_priority.csv`, `entity_registry.csv`, `document_entity_counts.csv`, `rolling_by_institute.csv`, `coverage_by_label.csv`, `date_anomalies.csv`, `validation.csv` et figures recalculées.

L'étape suivante pour augmenter la couverture est une résolution contextualisée des noms avec Wikidata/GeoNames et les textes intégraux ; le JSONL agrégé ne donne pas les passages pour lever toutes les ambiguïtés.
