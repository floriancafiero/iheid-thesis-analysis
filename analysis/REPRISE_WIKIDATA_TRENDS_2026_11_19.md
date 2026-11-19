# Reprise empirique : données doctorales, matching Wikidata et trajectoires (19 novembre 2026)

## Statut

Les calculs ont été exécutés hors ligne avec les données produites précédemment dans la conversation. Entrées : `iheid_catalog_recovery_results.zip` (1 730 doctorats corrigés, JSONL NER et métadonnées), `iheid_systematic_ner_2026.zip` (mentions NER directes normalisées), `iheid_wikidata_acteurs_extension.zip` (61 QID historiques vérifiés et alias acceptés), et l'artefact `wikidata-toutes-personnes-resultats` du [workflow terminé le 12 novembre](https://github.com/floriancafiero/iheid-thesis-analysis/actions/runs/43210889001).

**La branche principale reste inchangée.** Le code exécutable et tous les tableaux et quatre figures de cette reprise sont livrés dans l'archive attachée à la conversation `IHEID_reprise_wikidata_analyse_2026-11-19.zip`. Les gros fichiers source n'ont pas été ajoutés à Git.

## Correction prioritaire : doublons intersources

Sur les **1 730 enregistrements de doctorats** (HEI 742, IUED 23, IHEID 965), il existe **157 collisions titre normalisé + année + institut**. Une règle conservatrice ne considère comme doubles que les couples IHEID avec un identifiant ALTO/archives et un identifiant PDF numérique, et un rapport de longueur extraite d'au moins 0,995. Cela conduit à **109 doublons probables**, et donc à une sensibilité sur **1 621 enregistrements** (HEI 742, IUED 23, IHEID 856). Le fichier `duplicate_audit.csv` livré dans l'archive conserve la décision pour chaque collision. Les 48 autres collisions ne sont pas fusionnées, en particulier les volumes historiques et les titres génériques de doctorats qui pourraient être différents.

**Ne pas confondre :** 1 730 enregistrements de thèses et 1 621 enregistrements après correction ne sont pas nécessairement les nombres certains d'œuvres distinctes. La déduplication reste une hypothèse réversible ; les deux corpus sont exportés.

## Wikidata : trois canaux de confiance

1. **Registre vérifié** : les 61 QID d'acteurs historiques déjà examinés, associés seulement aux alias complets ou explicitement autorisés. 57 personnes effectivement détectées sur 1 621 enregistrements ; 386 couples thèse–personne.
2. **Provisoire** : 403 graphies multiterme avec QID humain unique et attribution Wikidata, mais non vérifiées dans les passages des thèses. La citoyenneté et la juridiction d'un poste ne valent pas sujet principal du texte. Ne pas injecter ces cas dans les courbes géographiques principales.
3. **Non résolu** : patronymes isolés, graphies communes, professions académiques mixtes, attributions multiples ou manquantes. Les 400 cas prioritaires ont reçu un tri automatique réversible, aucune annotation manuelle inventée.

**Exemples des corrections :** les noms simples `are`, `while`, `will` ne donnent plus de pays ; le QID de Charles de Gaulle et les noms complets de Churchill, Staline, etc. sont réintroduits uniquement depuis la liste d'alias antérieurement vérifiée, sans transformer leurs patronymes isolés en mentions fiables. Sumner Welles ne fait pas de Cuba le pays qu'étudie nécessairement une thèse américaine ; la fonction diplomatique Wikidata peut identifier le pays d'accréditation.

## Premiers résultats : proportions de thèses avec ≥5 mentions NER directes

| Corpus/institut | Décennie | Entité | Part |
| --- | --- | --- | ---: |
| HEI (41 thèses) | 1930–1939 | Société des Nations | 61,0 % |
| HEI (50) | 1950–1959 | ONU | 58,0 % |
| HEI (147) | 1980–1989 | ONU | 44,9 % |
| HEI (155) | 2000–2007 | CEE/CE/UE, famille stricte | 25,2 % |
| IHEID (483) | 2010–2019 | ONU | 33,1 % |
| IHEID (300) | 2020–2026 | ONU | 22,7 % |
| IHEID (483) | 2010–2019 | CEE/CE/UE, famille stricte | 13,0 % |
| IHEID (300) | 2020–2026 | CEE/CE/UE, famille stricte | 6,7 % |

Pour l'IHEID, comparaison 2010–2019 → 2020–2026 de pays directement cités ≥5 fois :
- États-Unis **53,0 % → 45,3 %** ;
- France **37,7 % → 29,7 %** ;
- Chine **20,9 % → 23,0 %** ;
- Inde **22,0 % → 21,7 %**.

La baisse de la France et des États-Unis demeure visible avec un seuil de **10 mentions**, et pour les États-Unis avec le seuil combiné 5 mentions / 2 pour 10 000 mots (23,2 % → 16,7 %). Cette évolution est **descriptive** et peut être affectée par citations, bibliographies, composition disciplinaire, langues et taille des textes. La décennie 2020 n'est pas achevée.

## Sensibilité des résultats aux doublons

Dans l'IHEID 2008–2009, ONU ≥5 passe de **38,6 % de 114 enregistrements** à **45,2 % de 73 enregistrements** après dédoublonnage (+6,6 points). Dans les années 2010, ONU ≥5 passe de **34,1 % à 33,1 %** ; dans les années 2020 de **22,5 % à 22,7 %**.

## Prochain contrôle scientifique indispensable

Les décomptes NER originaux ne donnent **aucune position de mention** dans le texte. Il est donc impossible de garantir qu'un nom apparaît dans le corps plutôt qu'en bibliographie. L'étape suivante est un contrôle stratifié de passages complets, avec vérification manuelle de l'identité du QID, du rôle de la personne et du véritable sujet de chaque thèse. Les 55 couples thèse–pays satisfaisant le critère fort « au moins deux personnalités vérifiées / au moins cinq mentions » concordent également avec ≥5 mentions directes du pays, mais ce constat ne valide pas automatiquement la pertinence thématique.

Les séries HEI et IHEID restent **séparées**, sans raccord artificiel en 2008. IUED (23 doctorats) n'est pas interprété comme série représentative. Aucune fusion URSS/Russie, RDA/Allemagne, SDN/ONU, ou ambiguïté de CEE/CE/UE n'est effectuée silencieusement.
