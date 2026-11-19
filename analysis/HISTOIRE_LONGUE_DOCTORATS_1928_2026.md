# Reprise de l'analyse des thèses sur toute la période, 1928–2026

**Date :** 19 novembre 2026. **Statut :** analyse descriptive révisée, série longue par institut.

## Pourquoi une analyse centenaire ?

La concentration antérieure sur 2010–2026 était insuffisante : le corpus documentaire corrigé commence en **1928**. Sur **1 730** doctorats initiaux (masters exclus), **109 doublons très probables** ont été écartés ; **1 621** enregistrements restent (742 HEI, 23 IUED, 856 IHEID). Les **109 doublons** concernent exclusivement l'IHEID en 2008–2022 ; les 742 doctorats historiques HEI de 1928 à 2007 sont inchangés.

La chaîne de l'IUED n'est **pas** couverte depuis 1961 : les 23 doctorats disponibles sont datés de 1999–2008, dont trois encore catalogués IUED en 2008. Les données IUED ne peuvent pas être interprétées comme une histoire complète de cet institut.

## Métrique

Proportion des doctorats ayant **≥5 mentions NER directes** de l'entité. Les seuils 3/5/10 sont comparables mais pas validés comme sujets. Les graphies NER sont plafonnées à 50 par type et par document ; bibliographie et corps ne sont pas distingués. Séparation stricte SDN/ONU et CEE/CE/UE (famille historique). Pas de fusion URSS/Russie. Les titres explicitement nommés fournissent seulement des contrôles positifs.

## Le mouvement institutionnel de longue durée (HEI, 1928–2007)

| Période | Doctorats | SDN | ONU | Construction européenne stricte | Banque mondiale |
|---|---:|---:|---:|---:|---:|
| 1928–1945 | 51 | 62,8% | 0,0% | 0,0% | 0,0% |
| 1946–1960 | 71 | 33,8% | 53,5% | 1,4% | 0,0% |
| 1961–1977 | 156 | 16,7% | 38,5% | 7,0% | 2,6% |
| 1978–1990 | 177 | 9,0% | 43,5% | 15,8% | 11,3% |
| 1991–2007 | 287 | 7,7% | 41,1% | 21,2% | 18,1% |

**Interprétation (hypothèse et non classification de sujets) :** la succession SDN→ONU, puis l'importance croissante de l'intégration européenne et des institutions économiques, s'observe sans disparition totale des références anciennes. Les taux de la SDN peuvent inclure la recherche historique rétrospective.

Les contrôles positifs par les titres donnent quatre thèses nommant explicitement la SDN dans les années 1930 et quatre nommant l'ONU dans les années 1950. Ces petits effectifs ne valident pas un sujet pour les autres thèses.

### Géographie

Pourcentage NER direct ≥5, HEI 1930s / HEI 1950s / HEI 1980s / HEI 2000–2007 / IHEID 2010s :

- États-Unis : **43,9 / 76,0 / 62,6 / 60,6 / 53,0**
- France : **61,0 / 70,0 / 53,1 / 53,5 / 37,7**
- Chine : **31,7 / 20,0 / 8,2 / 15,5 / 20,9**
- Inde : **12,2 / 24,0 / 18,4 / 16,1 / 21,9**
- Brésil : **7,3 / 10,0 / 14,3 / 18,1 / 17,8**

Cela ne soutient pas un récit linéaire de l'apparition « nouvelle » de la Chine ; elle est déjà bien représentée dans les mentions de l'HEI des années 1930. Ne pas confondre références géographiques avec sujets principaux.

### IHEID après 2008 : série distincte

- 2008–2019 : **556** doctorats ; ONU **34,7%**, famille européenne **13,5%**, Banque mondiale **23,0%**.
- 2020–2026 : **300** doctorats ; ONU **22,7%**, famille européenne **6,7%**, Banque mondiale **16,0%**.

Les différences récentes sont partiellement sensibles à la variation de langue et au volume de mots traités ; se reporter au rapport d'ajustement précédent. **Ne pas raccorder directement** les deux séries HEI et IHEID comme s'il s'agissait d'une population constante.

## Reproduction intégrale et livrables

Un paquet autonome a été produit dans la conversation : `IHEID_analyse_integrale_1928_2026.zip`. Il comprend :

- Les **cinq CSV d'entrée déjà disponibles** (métadonnées, audit doublons, NER pays, NER organisations, titres) ;
- Le script Python `IHEID_analyse_historique_1928_2026.py` sans accès réseau ;
- Les effectifs par décennie, les séries de pays/organisations depuis 1928, les huit périodes historiques, les titres explicites et les intervalles descriptifs Wilson ;
- **Cinq graphiques** (effectifs, HEI institutions, IHEID institutions, heatmap des pays 1930–2026, contrôle par les titres) ;
- Tests d'intégrité reproduisant les chiffres historiques.

Sources historiques : [Histoire de l'Institut](https://www.graduateinstitute.ch/fr/discover-institute/lhistoire-de-linstitut) ; [Archives et généalogie institutionnelle](https://libguides.graduateinstitute.ch/archives/historical_archives).

**Ne pas prendre les séries pour des annotations de sujets validées :** le top 50 NER, le bruit bibliographique et la variation de longueur des manuscrits restent les principales limites empiriques.
