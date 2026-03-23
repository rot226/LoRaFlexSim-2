# `scripts/`

## À quoi sert ce dossier ?

Ce dossier regroupe les scripts d'automatisation, de bootstrap, de lancement de campagnes, de génération de figures et de validation du dépôt.

## Quand l’utiliser ?

- Quand la documentation vous demande d'exécuter un script précis.
- Quand vous automatisez un workflow local, CI ou de campagne reproductible.
- Quand vous cherchez un utilitaire de tracé, de validation ou de comparaison déjà existant.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas au hasard pour découvrir le projet.
- Ne dupliquez pas ici une logique qui devrait vivre dans un package Python réutilisable.

## Point d’entrée / fichiers à ouvrir d’abord

- `scripts/bootstrap_windows.ps1` et `scripts/bootstrap_unix.sh` : préparation d'environnement.
- `scripts/loraflexsim.ps1` et `scripts/loraflexsim.sh` : wrappers vers le point d’entrée officiel `loraflexsim`.
- `scripts/windows/run_offline.ps1` : pipeline offline prioritaire pour Windows 11.
- `scripts/run_ci_pipeline.sh` : repère utile pour la chaîne de checks.
- `scripts/run_qos_comparison.py` ou les scripts `run_*.py` / `validate_*.py` pertinents selon le workflow ciblé.
