# `src/`

## À quoi sert ce dossier ?

Ce dossier contient la source Python packagée officiellement du projet, en particulier le package `mobilesfrdth` distribué et installé via `pip install -e .`.

## Quand l’utiliser ?

- Quand vous développez ou corrigez la CLI officielle `mobilesfrdth`.
- Quand un test ou une commande `python -m mobilesfrdth` renvoie vers ce package.
- Quand vous devez faire évoluer l'API packagée exposée aux utilisateurs.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas si vous travaillez uniquement sur le dashboard historique `loraflexsim/`.
- Ne commencez pas ici si vous cherchez seulement comment lancer le projet en tant qu'utilisateur.

## Point d’entrée / fichiers à ouvrir d’abord

- `src/mobilesfrdth/__main__.py` : entrée d'exécution du package.
- `src/mobilesfrdth/cli.py` : définition de la CLI officielle.
- `src/mobilesfrdth/config.py` et `src/mobilesfrdth/scenarios.py` : configuration et scénarios.
- `docs/user_guide_cli.md` : guide d'usage avant modification.
