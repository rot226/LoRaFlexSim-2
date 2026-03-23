# `loraflexsim/`

## Rôle de ce dossier

Ce dossier contient le cœur historique de LoRaFlexSim :

- le moteur de simulation ;
- le dashboard Panel ;
- les modules de scénarios et de validation associés.

## Position dans la surface publique

Après décision documentaire, la surface publique du simulateur est :

- **dashboard** : `panel serve loraflexsim/launcher/dashboard.py --show`
- **CLI officielle** : `loraflexsim ...`

Dans ce schéma, `loraflexsim/` reste central pour le **dashboard** et pour le **moteur historique**, mais ce dossier n’est pas lui-même la CLI packagée de haut niveau.

## Quand utiliser ce dossier ?

Utilisez `loraflexsim/` quand vous devez :

- modifier le dashboard ;
- intervenir sur le moteur historique ;
- déboguer `python -m loraflexsim.run` ;
- travailler sur les modules de `loraflexsim/launcher/`.

## Quand ne pas l’utiliser comme point de départ ?

Ne partez pas de ce dossier si votre besoin est seulement :

- lancer la CLI officielle utilisateur ;
- suivre le parcours communautaire standard ;
- documenter un premier usage.

Dans ces cas, orientez d’abord vers `README.md`, `docs/installation.md` et `docs/user_guide_cli.md`.

## Fichiers à ouvrir d’abord

- `loraflexsim/launcher/dashboard.py` : entrée principale du dashboard ;
- `loraflexsim/run.py` : entrée historique du moteur ;
- `loraflexsim/launcher/simulator.py` : orchestration centrale ;
- `docs/user_guide_dashboard.md` : guide du dashboard ;
- `docs/user_guide_cli.md` : guide de la CLI publique `loraflexsim`.
