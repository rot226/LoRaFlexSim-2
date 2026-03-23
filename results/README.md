# `results/`

## À quoi sert ce dossier ?

Ce dossier stocke des sorties de simulation, exports de validation et résultats synthétiques produits par les campagnes du dépôt.

## Quand l’utiliser ?

- Quand vous devez consulter un CSV, un JSON ou un sous-dossier déjà généré pour analyser une campagne.
- Quand un script ou une CLI écrit explicitement ses sorties dans `results/`.
- Quand vous comparez plusieurs exécutions ou validez des métriques de référence.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas comme point de départ pour comprendre comment lancer une campagne.
- Ne modifiez pas manuellement ces fichiers si la source attendue est un script reproductible.
- Ne l'utilisez pas pour stocker du code métier ou de la documentation générale.

## Point d’entrée / fichiers à ouvrir d’abord

- `results/README.md` : ce guide rapide.
- `results/validation_matrix.csv` : vue synthétique utile pour des vérifications globales.
- `results/qos_comparison/summary.json` : résumé d'une campagne QoS déjà agrégée.
- `docs/advanced_workflows.md` ou `docs/user_guide_cli.md` : pour retrouver le pipeline qui génère ces résultats.
