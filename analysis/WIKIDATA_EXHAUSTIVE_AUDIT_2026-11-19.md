# Audit du matching exhaustif Wikidata — 19 novembre 2026

## Sources et statut

- Dépôt : `floriancafiero/iheid-thesis-analysis`, branche `main` au commit `eb9657e561ac5788c552fbb37d5474311bd26783`.
- [Exécution GitHub Actions n° 43210889001](https://github.com/floriancafiero/iheid-thesis-analysis/actions/runs/43210889001) : **success**, terminée le 12 novembre 2026 à 22:20 UTC.
- Artefact final : `wikidata-toutes-personnes-resultats` (trois fichiers : `candidate_qids.csv`, `person_country_links.csv`, `coverage_report.json`), expiration GitHub annoncée au **10 février 2027**.
- L'exécution a fusionné **37 lots** et vérifié sans erreur réseau une ligne d'identité et une ligne filtrée pour chacune des 36 669 graphies.
- Ce document **n'affirme pas** que les pays ont déjà été recalculés sur les 1 730 thèses. Les grands fichiers locaux de NER/métadonnées doctorales ne sont pas dans le dépôt.

## Résultats quantitatifs vérifiés sur les CSV finaux

| Étape | Nombre de graphies |
|---|---:|
| Total de formes PER/PERSON dans la file | 36 669 |
| Un appariement exact de nom avec un humain Wikidata | 6 720 |
| Aucun nom humain exact reconnu | 26 278 |
| Plusieurs QID humains possibles | 3 671 |
| Exclues par le filtre académique | 3 184 |
| Conservées avec un pays | 1 447 (1 404 QID distincts) |
| Juridiction non mappée | 1 084 |
| Pays multiples ou manquants | 654 |
| Biographie insuffisante | 351 |

### Principales fragilités révélées

1. **Faux positifs du NER et de l'appariement par nom.** Parmi les 1 447 graphies conservées, **900 sont des graphies d'un seul token**, représentant **47 833 sur 58 883 occurrences NER associées aux graphies conservées (81,23 %)**. Elles incluent des noms authentiques, mais aussi des mots ordinaires tels que `are`, `while`, `will`, `you`, `several`. Les 900 ne sont pas tous des erreurs : c'est une catégorie **à risque** non encore vérifiée. Les chaînes composées comportent aussi des erreurs (`part ii`, `the italian`).
2. **Exclusion abusive de responsables historiques.** Parmi les graphies écartées comme « académiques », **994** ont pourtant au moins une fonction P39. Des figures comme Churchill, Roosevelt, Staline, Mussolini, Mao Zedong et François Mitterrand sont ainsi perdues. Notre ancienne règle « une seule occupation universitaire suffit à exclure » n'est pas compatible avec une mesure robuste des sujets diplomatiques et politiques.
3. **Juridictions impossibles à ramener naïvement à un pays unique.** **1 084** formes sont `unmapped_jurisdiction`, dont `de gaulle`, alors que le QID de Charles de Gaulle est correctement proposé. Les fonctions peuvent avoir plusieurs juridictions et des États historiques distincts. Il faut distinguer pays central, coprincipauté, poste supranational, nationalité et juridiction historique, sans convertir rétroactivement les États.
4. **Fondement géographique faible pour une majorité de liens.** Parmi les 1 447 graphies associées à un pays, **1 219** l'ont été par `citizenship_fallback` contre **228** par `political_office`. La nationalité n'est pas le pays qu'étudie une thèse.
5. **Écart entre identité et sujet.** La donnée NER ne contient que les comptes par document et non les offsets ni les sections de bibliographie. Aucun score de forte concentration ne garantit qu'une personne est **l'objet d'étude**, plutôt qu'une citation. Il faudra un échantillon de passages en texte intégral pour calibrer la précision.

**Attention aux dénominateurs :** ces nombres concernent des **graphies distinctes** (et les 58 883 mentions ci-dessus sont des totaux NER associés aux graphies retenues), non 1 447 thèses ni 1 404 personnes effectivement étudiées.

## Reproduire l'audit sans API

Décompresser ou transmettre directement le ZIP de l'artefact :

```bash
python analysis/audit_wikidata_quality.py \
  --artifact wikidata-results.zip \
  --top-per-issue 100 \
  --out results/wikidata/quality
```

Exports : `audit.json`, `manual_review_queue.csv` (400 lignes ; quatre sous-listes prioritaires de 100 : exclus académiques ayant P39, juridictions non mappées, mots isolés conservés, formes composées conservées). La queue est une **file de validation**, pas un jeu de vérité. Colonnes `manual_decision` et `review_note` laissées vides pour annotation.

## Suite scientifique, par ordre de priorité

1. **Contrôle humain stratifié** par statut, période, pays, longueur de graphie et fréquence ; évaluer précision de l'appariement et part de citations bibliographiques sur un échantillon de textes. Ne pas réintroduire sans validation l'ensemble des formes que le filtre rejette.
2. **Réviser la règle des occupations** : séparer indicateur « profil académique » et « fonction officielle » au lieu d'exclure automatiquement des personnalités à plusieurs carrières ; documenter les variantes strictes/sensibilité. Les membres de la bibliographie ne pourront être éliminés proprement qu'avec des positions dans le document.
3. **Réviser le mapping P39→pays** : garder toutes les fonctions et leurs dates, traiter les juridictions multiples et les États historiques comme des cas explicites, non des imputations automatiques. La nationalité doit rester un canal faible séparé.
4. **Recalculer la géographie des 1 730 thèses** seulement avec le corpus doctorat corrigé (HEI 742, IUED 23, IHEID 965), en séparant mentions directes de pays, acteurs vérifiés, nationalité de repli, présence dans le titre, et concordance. Conserver les fenêtres par institut (HEI 9 ans, IHEID 5 ans, IUED 15 ans à titre exploratoire), avec dénominateurs et intervalles d'incertitude. Pas de masters.
5. **Interprétation historique** : comparer les trajectoires SDN/ONU, construction européenne, décolonisation et diplomatie multipolaire, après validation des signaux, en évitant de raccorder artificiellement les instituts en 2008.

## Principe de sécurité analytique

**Ne pas brancher automatiquement `person_country_links.csv` sur les graphiques de pays existants.** La couverture exhaustive du pipeline API n'est ni une couverture exhaustive des personnes dans les textes, ni une mesure de qualité de l'appariement, ni une validation des sujets de thèse.
