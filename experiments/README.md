# `experiments/`

## À quoi sert ce dossier ?

Ce dossier regroupe des configurations, presets et sous-campagnes exploratoires utilisés pour la recherche, les comparaisons et certains essais reproductibles.

## Quand l’utiliser ?

- Quand vous devez charger un preset comme `default.yaml`, `paper_fast.yaml` ou `paper_core.yaml`.
- Quand vous travaillez sur une sous-campagne de recherche avec son propre README.
- Quand une validation ou une expérience renvoie explicitement vers `experiments/`.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas comme premier point d'entrée pour un nouvel utilisateur.
- Ne l'utilisez pas pour le flux standard si la documentation principale suffit.

## Point d’entrée / fichiers à ouvrir d’abord

- `experiments/default.yaml`, `experiments/paper_fast.yaml`, `experiments/paper_core.yaml` : presets principaux.
- `experiments/snir_stage1/README.md` et `experiments/ucb1/README.md` : guides locaux de sous-campagnes.
- `docs/advanced_workflows.md` : contexte de ces expériences dans l'ensemble du dépôt.
