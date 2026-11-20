# Personnes Wikidata : reprise indépendante des filtres géographiques et académiques

**20 novembre 2026 — Analyse de 1 621 doctorats HEI/IUED/IHEID (1928–2026)**

## Couverture

| Indicateur | Précédent | Nouveau |
|---|---:|---:|
| Thèses comportant au moins un QID de personne | 467/1 621 (28,8 %) | 1 184/1 621 (73,0 %) |
| Couples thèse–QID | 894 | 4 724 |
| QID distincts identifiés dans les nouvelles correspondances | — | 3 130 |

**729 thèses auparavant sans correspondance** sont nouvellement couvertes ; **455** restent couvertes dans les deux versions ; **12** anciennes correspondances ne sont plus retenues après contrôle (homonymies, noms d'éditeurs, prénoms sans patronyme). Gain net : 717 thèses.

Par institut : HEI 247→569 / 742 ; IUED 8→17 / 23 ; IHEID 212→598 / 856.

## Méthode et décisions

- Réutilise les résultats d'appariement Wikidata du workflow exhaustif (36 669 graphies), ainsi que le JSONL NER et le registre de 61 personnalités historiquement vérifiées.
- Un QID identifié pour une *personne* n'est plus exclu parce que sa nationalité, sa profession ou sa juridiction politique est absente ou ambiguë. Les professions académiques ne sont plus des motifs d'exclusion.
- Correspondances nouvelles acceptées lorsque le libellé d'un humain unique dans Wikidata et la graphie NER comportant plusieurs mots concordent. Les initiales + patronyme, variantes et alias vérifiés sont distingués comme canaux de preuve.
- Noms isolés (« Roosevelt », « Churchill », etc.) : **aucun nouveau QID par un patronyme seul** ; leurs fréquences ne sont utilisables qu'à titre supplémentaire si un nom complet et un QID concordants existent déjà dans **la même thèse**.
- Faux positifs manifestes écartés : mots courants, fragments NER, noms de maisons d'édition (« Edward Elgar », « Armand Colin », « Calmann-Lévy », etc.) et mentions indifférenciées (« l'auteur », « l'empereur »).
- Après identification seulement, les colonnes P27 (nationalité), P39 (fonction), P106 (profession) et le pays de l'ancien appariement géographique sont conservés comme **enrichissements facultatifs**. **3 244** couples ont une nationalité convertie en libellé à partir de nos mappings existants ; **1 365** n'ont pas de nationalité ou de rattachement géographique libellé.
- Niveaux de preuve des 4 724 couples : forme complète exacte 3 609 ; variante concordante 487 ; alias vérifié 386 ; initiale + nom 173 ; nom avec particule 69.

## Limites

Les listes NER sont plafonnées (souvent 50 graphies par type et document) et ne contiennent pas les contextes des occurrences. Il est **impossible**, avec ces seules données, de séparer systématiquement sujet de recherche, acteur mentionné et référence bibliographique ou de certifier les homonymes. Les nouveaux appariements sont donc **automatiques et encore à valider**, pas un gold standard. Un échantillon stratifié de 150 couples est préparé pour relecture ; aucun score de précision n'est revendiqué.

## Livrables produits

Le paquet autonome « IHEID_matching_Wikidata_personnes_corrige_2026-11-20.zip » a été généré dans la conversation, incluant :
- un CSV **à une ligne par thèse**, avec identifications Wikidata actualisées, disciplines, pays, lieux et organisations inchangés ;
- le fichier long des **4 724 couples thèse–personne** (QID, fréquence de nom complet, indicateurs de preuve et propriétés Wikidata) ;
- la décision pour chacune des **36 669 graphies**, la file des cas non retenus et un échantillon de contrôle ;
- le script Python autonome de reconstruction, ses entrées archivées et les tests d'intégrité, exécutés avec succès.

Les fichiers d'origine et les séries précédentes restent intacts. **Ce rapport ne marque pas les résultats comme vérifiés manuellement.**
