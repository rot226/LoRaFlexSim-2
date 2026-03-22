# `pretest_campagne/scenario_b/`

## En 30 secondes

| Rubrique | Réponse rapide |
| --- | --- |
| **À quoi sert ce dossier ?** | Regrouper les expériences de mobilité du scénario B de la campagne MNE3SD. |
| **Quand l’utiliser ?** | Quand vous devez rejouer des sweeps de portée, vitesse ou nombre de passerelles pour le scénario B. |
| **Quand ne pas l’utiliser ?** | Ne l’utilisez pas pour la CLI standard `mobilesfrdth`, ni pour un autre scénario `pretest_campagne`. |
| **Point d’entrée principal** | Les scripts `pretest_campagne.scenario_b.scenarios.run_mobility_*` ou le batch `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_b`. |
| **Sorties produites** | Des CSV dans `results/mne3sd/scenario_b/` et des figures dans `figures/mne3sd/scenario_b/`. |
| **Documentation détaillée** | Ce README documente les sweeps disponibles, les profils d’exécution et les commandes de génération. |

## Documentation détaillée

### Rôle du dossier

Ce dossier rassemble les scripts utilisés pour reproduire les expériences axées sur la mobilité du scénario B de la campagne MNE3SD.

### Scénarios couverts

- `urban_canyon`
- `rural_highway`
- `industrial_campus`

### Paramètres de simulation communs

Les points d'entrée des scénarios proposent notamment :

- `--config`
- `--seed`
- `--runs`
- `--duration`
- `--distance-min` / `--distance-max`
- `--speed-min` / `--speed-max`
- `--output` ou `--results`

### Profils d'exécution

Les lanceurs de scénarios respectent l'option `--profile` partagée ainsi que la variable d'environnement `MNE3SD_PROFILE` :

- `full` *(par défaut)*
- `ci`

### Parallélisation

Les scripts `run_mobility_range_sweep.py`, `run_mobility_speed_sweep.py` et `run_mobility_gateway_sweep.py` acceptent `--workers`.

### Sorties attendues

- CSV : `results/mne3sd/scenario_b/`
- Figures : `figures/mne3sd/scenario_b/`

### Générer les données

```powershell
python -m pretest_campagne.scenario_b.scenarios.run_mobility_range_sweep `
    --replicates 5 --seed 321 `
    --results results/mne3sd/scenario_b/mobility_range_custom.csv
```

### Générer les figures

```powershell
python -m pretest_campagne.scenario_b.plots.<figure_module> `
    --input results/mne3sd/scenario_b/<scenario_name>.csv `
    --figures-dir figures/mne3sd/scenario_b/ `
    --format pdf
```

### Lanceur de batch

```powershell
python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_b
```
