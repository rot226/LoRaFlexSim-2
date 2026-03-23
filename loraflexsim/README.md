# `loraflexsim/`

## À quoi sert ce dossier ?

Ce dossier contient le cœur applicatif historique de LoRaFlexSim, y compris le moteur de simulation Python, le dashboard et les modules de scénarios/validation associés.

## Quand l’utiliser ?

- Quand vous devez modifier le moteur historique LoRaFlexSim.
- Quand vous travaillez sur le dashboard ou les modules de `loraflexsim/launcher/`.
- Quand une commande ou un test pointe explicitement vers `loraflexsim.run` ou un module interne de ce dossier.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas comme premier point d'entrée pour un nouvel utilisateur.
- Ne privilégiez pas ce dossier si votre besoin relève uniquement de la CLI packagée `src/mobilesfrdth/`.

## Point d’entrée / fichiers à ouvrir d’abord

- `loraflexsim/run.py` : point d'entrée de lancement historique.
- `loraflexsim/launcher/dashboard.py` : entrée principale du dashboard.
- `loraflexsim/launcher/simulator.py` : orchestration centrale des simulations.
- `docs/user_guide_dashboard.md` : guide d'usage avant toute modification orientée dashboard.
