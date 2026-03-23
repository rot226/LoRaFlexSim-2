# `sfrd/`

## À quoi sert ce dossier ?

Ce dossier héberge une CLI SFRD avancée/spécialisée pour certaines campagnes ciblées, validations dédiées et traitements hors du flux standard `mobilesfrdth`.

## Quand l’utiliser ?

- Quand vous maintenez un pipeline SFRD déjà existant.
- Quand un workflow avancé mentionne explicitement `sfrd.cli`.
- Quand vous devez lancer une agrégation, une validation ou une calibration spécifique à SFRD.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas pour un premier contact avec le projet.
- Ne l'utilisez pas si la CLI officielle `mobilesfrdth` couvre déjà votre besoin.

## Point d’entrée / fichiers à ouvrir d’abord

- `sfrd/cli/run_campaign.py` : lancement de campagne.
- `sfrd/cli/validate_outputs.py` : validation des sorties.
- `sfrd/cli/calibrate_ucb.py` : calibration ciblée.
- `docs/advanced_workflows.md` : positionnement de `sfrd/` dans le dépôt.
