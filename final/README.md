# `final/`

## À quoi sert ce dossier ?

Ce dossier conserve un pipeline historique simple pour lancer des simulations, produire des CSV et générer rapidement des figures reproductibles.

## Quand l’utiliser ?

- Quand vous devez rejouer un flux historique minimal déjà utilisé dans le dépôt.
- Quand vous reproduisez un export CSV ou des figures existantes de `final/`.
- Quand une comparaison ou un document interne renvoie explicitement vers ce pipeline.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas comme flux principal moderne si `mobilesfrdth` répond déjà au besoin.
- Ne commencez pas ici pour découvrir l'architecture générale du dépôt.

## Point d’entrée / fichiers à ouvrir d’abord

- `final/run_all.ps1` et `final/run_all.sh` : lancement groupé historique.
- `final/scenarios/` : scénarios Python de référence pour ce flux.
- `final/plots/` : scripts de génération de figures.
- `docs/advanced_workflows.md` : contexte et positionnement du pipeline.
