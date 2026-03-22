# mobile-sfrd_th

> Archive legacy.
>
> Le **seul package Python canonique `mobilesfrdth`** vit désormais dans `src/mobilesfrdth/` à la racine du dépôt. Le doublon `mobile-sfrd_th/src/mobilesfrdth/` a été supprimé pour éviter toute ambiguïté lors du développement et de l'installation editable.

Ce dossier est conservé uniquement comme archive documentaire légère autour des anciens presets, exemples et tests exploratoires.

## Génération des figures depuis `aggregates/*.csv`

La commande de tracé lit **uniquement** les fichiers CSV produits par l'étape `aggregate`:

- `metric_by_factor.csv`
- `distribution_sf.csv`
- `convergence_tc.csv`
- `sinr_cdf.csv`
- `fairness_airtime_switching.csv`

Elle génère dans le dossier de sortie (`--out`) les figures minimales:

1. `fig01_pdr_vs_n_snir_off.png`
2. `fig02_pdr_vs_n_snir_on.png`
3. `fig03_der_vs_n_snir_off.png`
4. `fig04_der_vs_n_snir_on.png`
5. `fig05_throughput_vs_n_snir_off.png`
6. `fig06_throughput_vs_n_snir_on.png`
7. `fig07_tc_vs_speed.png`
8. `fig08_fairness_vs_n.png`
9. `fig09_sf_distribution.png`
10. `fig10_sinr_cdf.png`

Bonus (si données disponibles):

11. `fig11_airtime_vs_n.png`
12. `fig12_switch_count_vs_n.png`

### Exemple Windows 11 (PowerShell)

```powershell
# Depuis la racine du dépôt
mobilesfrdth plots `
  --aggregates-dir .\runs\aggregates `
  --out .\runs\plots
```

### Exemple avec filtres de scénario (PowerShell)

```powershell
mobilesfrdth plots `
  --aggregates-dir .\runs\aggregates `
  --out .\runs\plots_filtered `
  --scenario-filter mode=snir_on `
  --scenario-filter algo=ucb,legacy `
  --scenario-filter mobility_model=rwp
```

### Désactiver les figures bonus

```powershell
mobilesfrdth plots `
  --aggregates-dir .\runs\aggregates `
  --out .\runs\plots_minimal `
  --no-bonus
```

> En cas de données manquantes (fichier absent, colonne absente, lignes non numériques), la commande émet un warning explicite et ignore uniquement la/les figure(s) concernée(s).

## Presets de campagne (`experiments/`)

Presets disponibles via CLI :

```powershell
mobilesfrdth presets --list
```

Exemples de presets fournis :

- `paper_core` (config: `experiments/paper_core.yaml`)
- `paper_fast` (config: `experiments/paper_fast.yaml`)
- `safe` (force `time_bin_s=10` pour un calcul `Tc` stable/compatible protocole)

### Exécution preset en une commande

```powershell
# injecte automatiquement la grille + paramètres validés du preset
mobilesfrdth run --preset paper_core --out .\runs\paper_core
```

## Séquence prête à copier-coller (run → aggregate → plots → validate)

```powershell
# 1) Lister les presets
mobilesfrdth presets --list

# 2) Exécuter une campagne (preset principal)
mobilesfrdth run --preset paper_core --out .\runs\paper_core

# 3) Agréger les sorties
mobilesfrdth aggregate --results .\runs\paper_core --out .\runs\paper_core\agg

# 4) Générer les figures
mobilesfrdth plots --aggregates-dir .\runs\paper_core\agg\aggregates --out .\runs\paper_core\plots

# 5) Valider les prérequis agrégats (strict)
mobilesfrdth validate --aggregates-dir .\runs\paper_core\agg\aggregates --strict
```
