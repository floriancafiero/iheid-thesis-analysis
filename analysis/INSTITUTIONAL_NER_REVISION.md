# Rectification des séries historiques d'organisations

L'analyse a été reprise directement depuis le JSONL de NER du corpus doctoral corrigé (1 730 travaux, 1928–2026), et non des figures anciennes.

**Erreur corrigée :** la Société des Nations n'était pas absente. Le modèle de salience à deux régimes l'avait éliminée comme « non séparable », ce qui ne signifie pas absence de mentions. Après fusion stricte des variantes (société des nations, league of nations, SDN, Völkerbund...), elle totalise **7 459** mentions NER, contre **28 488** pour l'ONU.

**Entités et succession :** CEE/EEC, CE/EC et UE/EU restent distinctes historiquement mais sont aussi regroupées dans une famille analytique « construction européenne ». GATT et OMC sont conservés séparément et regroupés en « gouvernance commerciale ». La SDN et l'ONU ne sont jamais fusionnées. Les acronymes ambigus EC, EU, UN n'entrent pas dans la mesure stricte. L'extension de ces alias ferait passer les occurrences de l'intégration européenne de 15 033 à 27 623 et celles de l'ONU de 28 488 à 35 333 : sensibilité trop forte pour les agréger automatiquement.

**Périodisation :** 9 ans de fenêtre mobile centrée pour HEI (742 thèses, 1928–2007), 5 ans pour IHEID (965, 2008–2026), et 15 ans pour IUED (seulement 23 thèses datées, à titre exploratoire). Les courbes des institutions ne doivent pas être reliées en 2008. Les quatre périodes affichées sont 1927–1960 HEI, 1961–1976 HEI + précurseurs IUED, 1977–2007 HEI + IUED, depuis 2008 IHEID.

**Métrique :** % de thèses ayant au moins cinq mentions NER directes d'une organisation, avec sensibilité à trois et dix mentions, et intensité pour 100 000 mots. Ce n'est pas une probabilité validée de sujet principal de thèse.

**Exemples :** HEI années 1930 SDN 61 % ; HEI années 1950 ONU 58 % ; HEI années 1980 ONU 44,9 %, intégration européenne 13,6 % ; HEI 2000–2007 ONU 45,2 %, intégration européenne 25,2 % ; IHEID 2018–2022 ONU 22,0 %, intégration européenne 12,7 %. Une référence européenne isolée et anachronique dans les années 1930 rappelle les erreurs NER.

Les scripts complets, audits de variantes, tableaux annuels et figures HEI / IUED / IHEID sont livrés avec le présent échange dans iheid_revision_ner_instituts.zip. Le dépôt ne contient pas les grands fichiers du corpus original.

Repères historiques : https://www.graduateinstitute.ch/discover-institute/history-institute ; succession CEE/CE/UE : https://www.consilium.europa.eu/en/policies/how-eu-treaties-shaped-the-council-of-the-eu-and-the-european-council/ .
