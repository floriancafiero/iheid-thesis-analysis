# Reprise IHEID — analyse historique et audit Wikidata (19 novembre 2026)

## Résumé

**Deux univers à ne pas confondre :** la version corrigée du catalogue rassemble **1 730 enregistrements de thèses** (HEI 742, IUED 23, IHEID 965), de 1928 à 2026, sans masters. Un audit titre/année/institut et volume extrait quasi identique repère **109 doublons probables**, essentiellement ALTO/PDF : leur exclusion donne **1 621 enregistrements** (HEI 742, IUED 23, IHEID 856). La version dédoublonnée est une **analyse de sensibilité conservatrice**, pas une preuve que les 48 autres collisions de titres sont des œuvres distinctes. Les 109 suppressions ont un fichier de provenance (`duplicate_audit.csv`). Aucune fusion n'est appliquée aux manuscrits/volumes historiques HEI ou aux collisions incertaines.

**Appariement Wikidata :** 36 669 graphies PERSON/PER ont été traitées par le workflow achevé le 12 novembre. Le lien par nom à un humain Wikidata n'est pas une identification contextuelle. Nous reconstruisons donc trois canaux : (a) 61 QID d'un registre de personnalités politiques/diplomatiques anciennement contrôlées, avec alias stricts ; (b) 403 graphies supplémentaires ayant un appariement automatique multiterme plausible, **provisoires**, dans `identity_audit.csv` ; (c) les nombreux noms d'un seul token, cas académiques/biographiques et juridictions multiples, tenus à l'écart du signal principal. Les noms isolés ne renforcent une identité vérifiée que dans la même thèse si un alias complet vérifié est présent, et uniquement dans une colonne de **sensibilité**. On n'en fait aucune attribution automatique de sujet.

## Résultats principaux (corpus dédoublonné conservateur)

### 1. Les institutions internationales

Métrique : pourcentage des doctorats d'un institut et d'une décennie avec **au moins cinq mentions directes NER** de l'institution, variantes de noms strictement normalisées. Le tableau CSV exporte aussi les seuils 3 et 10 mentions. Les années 1920 (2 thèses) sont exclues des figures.

| Période | Entité | Thèses avec ≥5 mentions |
| --- | --- | ---: |
| HEI, 1930–1939 (n=41) | Société des Nations (SDN) | 61.0% |
| HEI, 1950–1959 (n=50) | Organisation des Nations unies (ONU) | 58.0% |
| HEI, 1980–1989 (n=147) | ONU | 44.9% |
| HEI, 2000–2007 (n=155) | Construction européenne (CEE→CE→UE), définition stricte | 25.2% |
| IHEID, 2010–2019 (n=483) | ONU | 33.1% |
| IHEID, 2020–2026 (n=300) | ONU | 22.7% |

On retrouve donc la centralité de la SDN dans le corpus des années 1930, puis de l'ONU après 1945. Les références tardives à la SDN ne sont pas anachroniques : l'organisation reste un objet d'étude rétrospectif. Au sein de l'IHEID, l'ONU est moins fréquemment mentionnée selon ce seuil en 2020–2026 qu'en 2010–2019 ; la construction européenne passe de 13.0% à 6.7%. Cela documente une évolution des **mentions**, pas nécessairement une perte d'intérêt scientifique ou de centralité politique. Les compositions disciplinaires, textuelles et linguistiques changent.

### 2. Pays dans les doctorats IHEID

| Pays | 2010–2019 (n=483) | 2020–2026 (n=300) | Écart |
| --- | ---: | ---: | ---: |
| United States | 53.0% | 45.3% | -7.7 pts |
| France | 37.7% | 29.7% | -8.0 pts |
| China | 20.9% | 23.0% | +2.1 pts |
| India | 21.9% | 21.7% | -0.3 pts |

La baisse relative des références aux États-Unis et à la France est plus nette que la hausse de la Chine. Sur les États-Unis, le signal plus exigeant (≥5 mentions et ≥2 pour 10 000 mots) passe de 23,2% à 16,7% ; la variation ne vient donc pas uniquement du seuil brut de cinq mentions. Pour la Chine, le signal strict de densité reste proche (10,4% à 11,0%). Ces différences sont des **hypothèses descriptives**, non des preuves d'une redistribution de l'attention : « France » et « Paris » peuvent notamment apparaître dans les références institutionnelles et bibliographiques. Les courbes HEI et IHEID sont montrées séparément ; leurs décennies 2000 ne sont pas assimilables à un même échantillon.

### 3. Personnalités Wikidata

Dans les 1 621 enregistrements après dédoublonnage, **57 personnalités distinctes du registre de 61** sont effectivement retrouvées par au moins un alias complet. Leurs graphies exactes produisent **386 couples thèse–personne** ; **266 couples thèse–pays** ont au moins cinq mentions d'acteurs contrôlés, mais **55** seulement citent deux acteurs distincts d'un même pays et au moins cinq occurrences au total. Ces 55 ont aussi cinq mentions directes du pays. Ce n'est **pas** une validation de sujet de thèse, parce que les références de bibliographie ne sont pas isolées.

Exemples réels (titres et décomptes reliés au catalogue) : « *Ideological trends and economic reform in China, (1978–1993)* » (HEI, 1994) mentionne dans les NER Deng Xiaoping, Hu Yaobang, Mao Zedong et Jiang Zemin ; « *Les français face à la réunification allemande* » (HEI, 2002) mentionne de Gaulle, Mitterrand, Chirac et Giscard d'Estaing. Ces rapprochements sont plus interprétables que l'attribution du pays d'une personne qui ne figure qu'en bibliographie. Ils restent des exemples, non une validation globale.

Les appariements Wikidata nouveaux restent dans un fichier **provisoire** : notamment 403 graphies multiterme, dont le QID et le pays peuvent être trompeurs. Exemple problématique : Sumner Welles, diplomate américain, est rattaché à Cuba par la juridiction Wikidata d'un poste ; le pays du poste n'est pas toujours celui représenté. Nous évitons donc de convertir mécaniquement P39 ou P27 en « pays étudié ».

### 4. Effet du dédoublonnage

Au sein de l'IHEID 2008–2009, l'ONU passe de **38,6%** sur 114 enregistrements à **45,2%** sur 73 après retrait des doublons probables, soit +6,6 points de pourcentage. La correction a des effets plus modestes sur 2010–2019 (34,1% → 33,1%) et 2020–2026 (22,5% → 22,7%). Le fichier `compare_organizations_raw_vs_dedup.csv` permet de contrôler tous les écarts entité par entité.

## Procédure, limites et reproduction

Les données NER sont des **comptages par document** : aucun offset de mention, aucune détection fiable des sections bibliographiques, aucune mesure directe des thèmes de thèse. Les dates anciennes peuvent être affectées par l'OCR, les professions P106 et pays P27/P39 par les lacunes de Wikidata. Ne pas fusionner URSS/Russie, RDA/Allemagne, SDN/ONU ni CEE/CE/UE (sauf famille explicitement étiquetée). Le n IUED=23 empêche toute série interprétable à l'échelle décennale.

Reproduction après récupération des **fichiers sources originaux** : `doctoral_ner_recovered.jsonl.zip` et `doctoral_metadata_recovered.csv` (archive `iheid_catalog_recovery_results.zip`), `document_entity_counts.csv` (archive `iheid_systematic_ner_2026.zip`), deux CSV de l'artefact final GitHub Actions du 12 novembre 2026 et `expanded_registry_strict_full_names.csv` (archive `iheid_wikidata_acteurs_extension.zip`). Les entrées volumineuses ne sont pas copiées dans ce ZIP de diffusion. Le script `rebuild_iheid_trends.py` et quatre tests sont fournis.

```bash
python rebuild_iheid_trends.py --ner doctoral_ner_recovered.jsonl.zip \
    --metadata doctoral_metadata_recovered.csv \
    --entity-counts document_entity_counts.csv \
    --candidates candidate_qids.csv \
    --screened person_country_links.csv \
    --curated expanded_registry_strict_full_names.csv \
    --out results_dedup --dedup-strong
python -m unittest test_rebuild_iheid_trends.py
```

**Étape suivante** : contrôle manuel stratifié, sur textes complets, du statut des mentions (corps/notes/bibliographie) et validation des QID automatiques. Les `manual_decision` restent vierges dans `review_queue_auto_triage.csv` ; seule une première classification automatique à faible risque a été ajoutée. Sans ce corpus de vérité, les indicateurs ne peuvent être présentés que comme une cartographie des mentions.
