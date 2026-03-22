# `scripts/`

Ce dossier regroupe les **scripts d’automatisation, de bootstrap, de validation et d’orchestration** du dépôt.

## Repères rapides

- `bootstrap_windows.ps1` / `bootstrap_unix.sh` : préparation de l’environnement ;
- `mobilesfrdth.ps1` / `mobilesfrdth.sh` : wrappers dépôt vers la CLI officielle ;
- `windows/` : scripts Windows dédiés ;
- `mne3sd/` : orchestration de campagnes MNE3SD ;
- `run_*.py`, `plot_*.py`, `validate_*.py` : scripts ciblés de campagne, tracé ou contrôle.

## Quand l’utiliser ?

Quand la documentation vous demande un script précis ou quand vous automatisez un workflow local/CI.

## Quand ne pas l’utiliser ?

Si vous découvrez le projet, ne parcourez pas ce dossier au hasard : commencez par le `README.md` racine, puis utilisez `mobilesfrdth` ou le dashboard.
