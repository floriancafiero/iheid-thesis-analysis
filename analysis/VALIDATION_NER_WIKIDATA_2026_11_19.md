# Validation Wikidata et NER : audit complémentaire du 19 novembre 2026

## Périmètre
Le corpus de départ comporte **1 730 enregistrements doctoraux**, exclusivement (HEI 742 ; IUED 23 ; IHEID 965). L'analyse de sensibilité dédoublonnée porte sur **1 621 documents**, après retrait *probable* de 109 doublons (et non une correction définitive des sources). Le travail précédent avait 157 paires de titres identiques (même année/institut), dont 48 restant non résolues.

## Découverte critique : tronquage systématique à 50 graphies

Le JSONL historique **n'est pas une liste exhaustive des entités par thèse**. Le champ `entities_by_type` contient au plus **50 formes par type** dans chaque document.

| Type | Documents ayant ce type | Documents affichant exactement 50 formes |
|---|---:|---:|
| PER | 1 254 | 1 250 |
| PERSON | 476 | 476 |
| ORG | 1 730 | 1 726 |
| GPE | 476 | 470 |
| LOC | 1 729 | 1 360 |
| NORP | 476 | 247 |

La formule précédente « 36 669 graphies traitées exhaustivement par Wikidata » doit être comprise **exhaustive relativement à cet inventaire NER plafonné**, **pas exhaustive relativement aux mentions présentes dans les textes intégraux**. Les absences ne sont pas interprétables, notamment pour les individus relativement peu cités. Les distributions thématiques et géographiques dérivées de la présence des entités demandent donc un nouveau NER sans plafond avant d'être considérées complètes.

## Échantillon d'appariements

Sur les sorties `person_doc_links.csv` du corpus dédoublonné, 894 couples (thèse, QID) sont disponibles : 386 correspondances du registre de personnes vérifiées, 314 correspondances automatiques avec nationalité de repli, 192 avec fonction officielle et 2 autres. **508 couples automatiques ne sont pas validés.**

Une file **stratifiée reproductible de 120 couples** a été constituée, répartie comme suit :
- 42 du registre vérifié ;
- 38 automatiques P39 / fonction ;
- 38 automatiques P27 / citoyenneté ;
- 2 autres cas automatiques.

La stratification couvre les périodes des instituts et des fréquences faibles/fortes. **Ce n'est pas un estimateur non biaisé de précision** ; les catégories à risque sont volontairement suréchantillonnées.

Seuls trois couples du fichier comportent une personne désignée *par son nom complet dans le titre* : Roosevelt (HEI 1989), Getúlio Vargas (HEI 1981), et François Mitterrand (HEI 2002). Ils fournissent un indice positif de pertinence au niveau du titre, mais ne valident pas l'identité ou l'usage des autres mentions. Les autres noms ne sont **ni des références seulement, ni des sujets validés** par défaut : statut « non vérifié ».

## Doublons et contrôle de NER

Sur les 157 paires titre/année/institut, 109 ont une concordance OCR/PDF et presque exactement le même nombre de mots (moins de 0,5 % d'écart). Leurs exclusions restent une **analyse de sensibilité**. Les 48 autres paires ne sont pas fusionnées automatiquement, notamment les titres génériques `Three essays in development economics`.

La similarité des principaux comptes NER entre deux versions d'une thèse peut être modeste, du fait du plafonnement top 50 et des différences entre extractions. Un cosinus de comptes NER ne permet donc **pas** de décider à lui seul de l'identité textuelle. Les scripts de validation livrés séparément produisent `duplicate_ner_similarity.csv` et une liste de revue des 48 cas.

## Appariements connus comme problématiques

- `are`, `while`, `will` : QID humains possibles mais graphies ordinaires ; conservées hors des appariements exploités.
- `churchill`, `roosevelt`, `staline` : noms simples conservés en attente de désambiguïsation.
- `de gaulle` : conservé via le registre vérifié.
- `Sumner Welles` : exemple où P39 suggère **Cuba** (lieu de fonction), ce qui n'est pas un pays dont la thèse traiterait nécessairement, ni son pays représenté.

## Limite de validation textuelle

Les archives récupérées contiennent les **comptages NER agrégés**, pas les textes intégraux des doctorats ni les offsets des mentions. Impossible donc pour l'instant de distinguer sérieusement corps, notes, bibliographies ou sujet principal ; **aucun pourcentage de précision/rappel ni accord inter-annotateurs n'est annoncé**.

Les fichiers livrés dans la conversation comportent :
- un script de diagnostic et un **CSV de 120 cas** préformaté pour deux lecteurs indépendants ;
- une liste de **48 titres ambigus** ;
- un contrôle du plafond NER ;
- un script d'extraction de concordances *activable lorsqu'on récupère les TXT originaux* (marquage bibliographique purement indicatif) ;
- des tests reproductibles.

**Prochain verrou scientifique :** retrouver les TXT ALTO/PDF originaux et relancer l'extraction sans top 50, puis vérifier par double annotation stratifiée QID, position et rôle thématique. Tant que cette vérification n'est pas possible, les graphiques restent des cartes exploratoires des **mentions NER les plus fréquentes**, et non des sujets avérés des thèses.

Sources internes : `analysis/rebuild_iheid_trends.py` sur cette branche et les entrées originales `doctoral_ner_recovered.jsonl.zip`, `doctoral_metadata_recovered.csv`, `person_doc_links.csv`.