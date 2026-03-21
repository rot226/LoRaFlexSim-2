# Rapport d'exécution du pipeline scénario C (SNIR OFF/ON + tailles 80..1280)

## 1) Test rapide

Commande lancée depuis la racine du dépôt sous Windows 11 / PowerShell :

```powershell
python -m pretest_campagne.scenario_c.run_all --allow-non-scenario-c --clean-hard --network-sizes 80 --replications 1 --seeds_base 1 --snir_modes snir_off,snir_on
```

Résultat : exécution terminée, sorties Step1+Step2 produites, puis validation globale réussie (`Aucune anomalie résultats détectée.`).

## 2) Campagne complète demandée

### Step1 (SNIR OFF+ON)

```powershell
python -m pretest_campagne.scenario_c.step1.run_step1 --network-sizes 80 160 320 640 1280 --replications 5 --seeds_base 1 --snir_modes snir_off,snir_on --workers 1
```

### Step2 (algorithmes ADR, MixRA-H, MixRA-Opt, UCB1-SF)

```powershell
python -m pretest_campagne.scenario_c.step2.run_step2 --network-sizes 80 160 320 640 1280 --replications 5 --seeds_base 1 --workers 1
```

### Agrégation finale

```powershell
@'
from pathlib import Path
import pandas as pd

for step in ["step1", "step2"]:
    base = Path("results/pretest_campagne/scenario_c") / step
    out = base / "aggregates"
    out.mkdir(parents=True, exist_ok=True)
    files = sorted((base / "by_size").glob("size_*/aggregated_results.csv"))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df.to_csv(out / "aggregated_results.csv", index=False)
    print(step, "rows", len(df))
'@ | python -
```

Résultat agrégats :
- `step1 rows 600`
- `step2 rows 400`

## 3) Validation de sortie

Commande de validation principale :

```powershell
python -m pretest_campagne.scenario_c.validate_results --step1-dir results/pretest_campagne/scenario_c/step1 --step2-dir results/pretest_campagne/scenario_c/step2
```

Résultat : `Aucune anomalie résultats détectée.`

## 4) Contrôle manuel d'un échantillon (anti-mélange OFF/ON + cohérence numérique)

Vérification manuelle par script Python :

- Step1 : modes SNIR observés = `['snir_off', 'snir_on']`.
- Step2 : mode SNIR observé = `['snir_on']`.
- Comptages `network_size × algo × snir_mode` cohérents (20 lignes par combinaison affichée dans l'échantillon).
- Cohérence numérique :
  - `step1 pdr_mean out_of_range = 0`
  - `step2 success_rate_mean out_of_range = 0`
  - `step2 reward_mean out_of_range = 0`

Extraits observés :
- Step1 (`network_size=1280`, `algo=adr`) contient des lignes distinctes `snir_off` et `snir_on`.
- Step2 (`network_size=1280`) contient des valeurs `success_rate_mean` et `reward_mean` dans [0,1] pour ADR/MixRA-H.

## 5) Note sur `verify_all`

`python -m pretest_campagne.scenario_c.tools.verify_all --replications 5` retourne un échec non bloquant lié à un CSV externe manquant de données :

- `CSV sans ligne de données: pretest_campagne/scenario_c/common/data/author_curves.csv`

Ce point n'affecte pas la validation des résultats simulés Step1/Step2 ni la cohérence des agrégats produits dans cette campagne.
