# `pretest_campagne/scenario_d/`

## En 30 secondes

| Rubrique | Réponse rapide |
| --- | --- |
| **À quoi sert ce dossier ?** | Regrouper les expériences de mobilité du scénario D de la campagne MNE3SD et leurs variantes D1–D10. |
| **Quand l’utiliser ?** | Quand vous devez rejouer ou ajuster une campagne de mobilité scénario D avec sweeps de portée, vitesse, passerelles ou charge. |
| **Quand ne pas l’utiliser ?** | Ne l’utilisez pas pour une campagne standard `mobilesfrdth` ni pour les autres scénarios `pretest_campagne`. |
| **Point d’entrée principal** | Les scripts `pretest_campagne.scenario_d.scenarios.run_mobility_*` ou le batch `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_d`. |
| **Sorties produites** | Des CSV dans `results/mne3sd/scenario_d/` et des figures dans `figures/mne3sd/scenario_d/`. |
| **Documentation détaillée** | Ce README résume les scénarios D1–D10, les paramètres communs et les commandes de génération. |

## Documentation détaillée

### Rôle du dossier

Ce dossier rassemble les scripts utilisés pour reproduire les expériences axées sur la mobilité du scénario D de la campagne MNE3SD.

### Scénarios D1–D10

| Scénario | Nom | Objectif |
| --- | --- | --- |
| D1 | `mobility_range_baseline` | Référence de portée moyenne avec mobilité piétonne. |
| D2 | `mobility_range_stress` | Robustesse en portée maximale avec bruit de canal accru. |
| D3 | `mobility_speed_baseline` | Impact d'une vitesse nominale sur le PDR. |
| D4 | `mobility_speed_extremes` | Exploration des vitesses extrêmes. |
| D5 | `mobility_gateway_baseline` | Distribution du trafic par passerelle. |
| D6 | `mobility_gateway_density` | Gain marginal d'ajout de passerelles. |
| D7 | `mobility_model_comparison` | Comparaison des modèles de mobilité. |
| D8 | `mobility_interference_load` | Effet d'une charge radio accrue. |
| D9 | `mobility_reliability_ci` | Jeu rapide pour validations CI. |
| D10 | `mobility_full_campaign` | Campagne complète du scénario D. |

### Paramètres de simulation communs

Les scripts exposent notamment : `--seed`, `--runs`, `--duration`, `--distance-min`, `--distance-max`, `--speed-min`, `--speed-max`, `--output` ou `--results`, ainsi que `--profile` et `--workers` selon le sweep.

### Sorties attendues

- CSV : `results/mne3sd/scenario_d/`
- Figures : `figures/mne3sd/scenario_d/`

### Générer les données

```powershell
python -m pretest_campagne.scenario_d.scenarios.run_mobility_range_sweep `
    --replicates 5 --seed 321 `
    --results results/mne3sd/scenario_d/mobility_range_custom.csv
```

### Générer les figures

```powershell
python -m pretest_campagne.scenario_d.plots.<figure_module> `
    --input results/mne3sd/scenario_d/<scenario_name>.csv `
    --figures-dir figures/mne3sd/scenario_d/ `
    --format png
```

### Lanceur de batch

```powershell
python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_d
```
