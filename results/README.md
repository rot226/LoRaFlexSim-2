# `results/`

## Positionnement du dossier dans LoRaFlexSim-2

Le dossier `results/` regroupe des **sorties versionnées**, des exports consolidés et des
artefacts de validation conservés dans le dépôt pour documenter des campagnes déjà
exécutées. Dans LoRaFlexSim-2, il sert donc surtout de **référence d'analyse**, d'**archive
reproductible** et d'**exemple concret de résultats attendus**, plutôt que de point de départ
pour lancer une nouvelle simulation.

## Statut du contenu

- **Archive / référence** : les fichiers présents servent à relire des résultats historiques,
  à comparer des métriques ou à appuyer une reproduction.
- **Exemple de sorties** : plusieurs sous-fichiers montrent la forme attendue des CSV, JSON ou
  agrégats générés par les pipelines du dépôt.
- **Sorties versionnées** : certains résultats sont volontairement suivis dans Git pour garder
  un état de référence stable entre validations.

## Quand consulter `results/`

- Quand vous devez **relire des résultats déjà produits** sans relancer immédiatement une campagne.
- Quand une documentation, un test, un script d'analyse ou une comparaison scientifique cite
  explicitement un fichier situé dans `results/`.
- Quand vous cherchez un **exemple de format de sortie** attendu avant d'automatiser une
  post-analyse.
- Quand vous comparez une nouvelle exécution à une **référence versionnée** du dépôt.

## Quand ne pas l'utiliser comme point d'entrée

- Ne commencez pas par `results/` pour découvrir **comment installer, lancer ou configurer**
  LoRaFlexSim-2.
- N'utilisez pas ce dossier comme source canonique du workflow principal : pour démarrer,
  ouvrez plutôt `README.md`, puis `docs/user_guide_dashboard.md` ou
  `docs/user_guide_cli.md`.
- N'y ajoutez pas manuellement de logique métier, de documentation générale ou de résultats
  ad hoc non reliés à un pipeline reproductible.
- Si votre objectif est de **produire** de nouvelles sorties, partez des scripts, scénarios,
  commandes CLI et guides du dépôt ; `results/` ne documente que les artefacts déjà générés.

## Point d'entrée / fichiers à ouvrir d'abord

- `results/README.md` : ce guide rapide.
- `results/validation_matrix.csv` : vue synthétique utile pour des vérifications globales.
- `results/qos_comparison/summary.json` : résumé d'une campagne QoS déjà agrégée.
- `docs/advanced_workflows.md` ou `docs/user_guide_cli.md` : pour retrouver le pipeline qui génère ces résultats.

## Synthèse secondaire : preset `flora_hata`

Le preset `flora_hata` apparaît dans `results/` comme **référence longue portée** déjà
calculée, notamment via `results/long_range.csv`. Il correspond au profil FLoRa basé sur Hata
utilisé dans les comparaisons longue distance du dépôt.

À consulter surtout si vous voulez :

- relire une **valeur de référence** associée aux campagnes longue portée ;
- comparer une nouvelle exécution LoRaFlexSim à un export déjà versionné ;
- retrouver un exemple de sortie lié aux presets `flora`, `flora_hata` et dérivés.

Pour comprendre ou relancer le scénario, utilisez d'abord `docs/long_range.md`,
`docs/reproduction_flora.md` et la CLI `python -m loraflexsim.run --long-range-demo ...` ; la
présence de `flora_hata` dans `results/` ne remplace pas ces points d'entrée.
