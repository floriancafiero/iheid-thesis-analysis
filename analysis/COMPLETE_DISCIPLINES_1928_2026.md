# Classement intégral des disciplines des doctorats (1928–2026)

**Révision du 20 novembre 2026 — classification à partir des titres et sous-titres.**

Cette mise à jour résout la demande de **classer les 331 thèses encore « indéterminées » dans la version prudente** (318 HEI et 13 IUED).

## Résultats des 331 reclassifications

| Discipline proposée | Effectif |
|---|---:|
| Science politique / relations internationales | 100 |
| Économie | 81 |
| Histoire | 76 |
| Droit | 47 |
| Études du développement interdisciplinaires | 15 |
| Anthropologie / sociologie | 11 |
| Psychologie / psychologie sociale | 1 |
| **Total** | **331** |

**Confiance de lecture du titre :** 191 relativement explicites, 38 moyens, **102 faibles**. Même une confiance « élevée (titre) » **ne constitue pas** une validation de la discipline universitaire. Une discipline alternative est conservée lorsque plausible.

Deux tableaux exhaustifs sont publiés dans ce dossier :

1. [331_titles_reclassified.csv](./results_2026_11_20/331_titles_reclassified.csv) : `doc_id`, titre et sous-titre, discipline proposée, alternatives, niveau de confiance, ancienne classification et justification. Les lignes sont identifiées par `doc_id` ; `index_audit` n'est qu'un ordre de lecture.
2. [1621_disciplines_completees.csv](./results_2026_11_20/1621_disciplines_completees.csv) : corpus complet de 1 621 doctorats, discipline remplie pour chacun, ancienne version prudente, code officiel le cas échéant, provenance et degré de confiance.

Les 856 codes de discipline des doctorats de **l'IHEID 2008–2026** sont **préservés**. Les 765 HEI/IUED n'ont **pas** de classification administrative confirmée : leurs étiquettes sont proposées, non observées.

## Pourquoi ne pas confondre « aucune case vide » et « classification exacte »

Le premier modèle supervisé par les titres récents donnait environ 73 % de bonnes prédictions en validation croisée sur les doctorats de l'IHEID dont la discipline est attestée. La relecture sémantique des titres historiques permet de proposer une classe à toutes les notices restantes, mais **sa précision n'a pas été mesurée sur des thèses anciennes annotées**.

Exemples d'ambiguïtés :
- L'Assemblée générale des Nations Unies : politique institutionnelle **ou** droit des organisations internationales.
- The evolution of the Suez Canal Status from 1869 up to 1956 : histoire **et** droit.
- Trade negotiations at the GATT : économie internationale **ou** relations internationales.
- Psychopathologie de la violence : psychologie, distincte des six catégories usuelles de l'Institut.

Les thèses des programmes historiques ne doivent pas être automatiquement rattachées aux **programmes contemporains** ; notamment, « études du développement » est ici une catégorie analytique interdisciplinaire et non un code de diplôme ancien.

## Pour les visualisations historiques

Éviter de présenter les séries de l'HEI pré-2008 (disciplines déduites des titres) et de l'IHEID post-2008 (codes officiels) comme homogènes. Il convient de :
- distinguer visuellement **classification inférée** et **classification officielle** ;
- donner les effectifs par institut et période ;
- effectuer une sensibilité en excluant les 102 nouvelles classifications de faible confiance ;
- présenter les catégories du corpus ancien comme des **profils disciplinaires probables**, pas comme la structure réelle des départements.

Le classeur Excel complet, incluant un onglet dédié aux 102 cas fragiles, a été généré comme fichier de travail téléchargeable dans la conversation.
