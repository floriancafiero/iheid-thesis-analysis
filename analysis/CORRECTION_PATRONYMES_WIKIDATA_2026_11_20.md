# Rapprochement des patronymes et QID — correction transversale (20 novembre 2026)

## Résultat

Recalcul hors-ligne du corpus doctoral HEI/IUED/IHEID de 1928 à 2026 (1 621 thèses dédoublonnées) à partir des NER archivées et du matching Wikidata de 36 669 graphies.

- Couverture des thèses avec au moins un QID humain : **1 184 → 1 355 / 1 621**, soit **83,6 %**.
- Liens thèse–QID : **4 724 → 5 858**. Les 2 liens « M. Churchill » → Morgan Churchill, dont la preuve ne repose que sur une initiale ambiguë, ont été mis en quarantaine ; **1 136 nouveaux liens** reposent sur des patronymes sans nom complet dans la même thèse.
- Mentions de patronyme attribuées : 63 390. QID distincts après correction : 3 149.
- Les identifications sont *automatiques* et ne prouvent pas que la personne est le sujet de la thèse ou mentionnée hors bibliographie.

## Identités historiques auparavant sous-estimées

| Personne | Ancien nombre de thèses | Nouveau |
|---|---:|---:|
| Adolf Hitler | 4 | 79 |
| Joseph Staline | 2 | 64 |
| Benito Mussolini | 1 | 39 |
| Vladimir Lénine | 0 | 48 |
| Winston Churchill | 8 | 40 |
| Hans Kelsen | 15 | 52 |
| Karl Marx | 0 | 53 |
| Michel Foucault | 12 | 58 |

## Règles de rapprochement

1. Préserver toute identité ayant une forme complète compatible dans la thèse.
2. Attribuer des occurrences de patronyme à cette identité si elle est la seule compatible dans le document.
3. Autoriser une correspondance autonome uniquement si une forme complète du QID est attestée dans le corpus, si le patronyme ne présente aucune autre identité détectée et s'il n'est ni mot-outil ni toponyme. Les variantes historiquement distinctives très connues (Hitler, Stalin/Staline, Lenin/Lénine, Churchill, etc.) sont répertoriées à part comme exceptions éditoriales auditables.
4. **Ne pas décider arbitrairement** pour Roosevelt, Gandhi, Kennedy, Bush, Wilson, Mao, Koskenniemi, Clapham, Morgenthau, etc. Leurs patrons nominaux sont disponibles dans une **seconde série sans QID forcé**.
5. Conserver les champs bibliographiques, disciplines, pays, lieux et organisations tels quels : aucun rattachement géographique de personne n'est inventé.
6. Conserver un audit thèse–patronyme–QID–type de preuve, les liens invalidés et les cas non résolus.

## Reproductibilité

Le paquet `IHEID_patronymes_Wikidata_corriges_1928_2026.zip` fourni dans la conversation contient le script `corriger_patronymes_wikidata_iheid.py`, le script de graphes, 10 tests d'intégrité exécutés avec succès, les entrées archivées, la table longue corrigée, le CSV à 1 621 thèses, les séries décennales et cinq graphiques.

Les données d'entrée NER sont souvent tronquées aux 50 formes les plus fréquentes par type et par thèse. Ce travail n'est ni une validation exhaustive d'identité ni une validation des sujets étudiés. Les courbes sont des tendances de mentions.
