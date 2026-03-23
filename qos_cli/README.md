# `qos_cli/`

## À quoi sert ce dossier ?

Ce dossier centralise les scripts QoS spécialisés qui préparent les scénarios, lancent les simulations LoRaFlexSim, agrègent les métriques, produisent les figures et génèrent un rapport synthétique.

## Quand l’utiliser ?

- Quand vous exécutez une campagne QoS complète.
- Quand vous explorez des variantes avancées comme les balayages, surfaces, scatter plots ou forçages SNIR.
- Quand un workflow mentionne explicitement `python -m qos_cli.lfs_run` ou un autre script `lfs_*`.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas comme CLI principale si le flux standard `mobilesfrdth` suffit.
- Ne commencez pas ici si vous ne travaillez pas explicitement sur un scénario QoS spécialisé.

## Point d’entrée / fichiers à ouvrir d’abord

- `qos_cli/lfs_run.py` : point d'entrée principal pour lancer une campagne.
- `qos_cli/scenarios.yaml` : définition des scénarios QoS.
- `qos_cli/lfs_metrics.py`, `qos_cli/lfs_plots.py`, `qos_cli/lfs_report.py` : post-traitement, figures et rapport.
- `docs/advanced_workflows.md` : positionnement de cette CLI spécialisée.
