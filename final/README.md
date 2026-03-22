# `final/`

## En 30 secondes

| Rubrique | Réponse rapide |
| --- | --- |
| **À quoi sert ce dossier ?** | Conserver un pipeline historique simple pour lancer une simulation, écrire des CSV et générer des figures rapidement. |
| **Quand l’utiliser ?** | Quand vous devez reproduire un export CSV/figures existant, préparer une comparaison rapide ou rejouer un flux historique minimal. |
| **Quand ne pas l’utiliser ?** | Ne l’utilisez pas comme flux principal moderne si la CLI `mobilesfrdth` couvre déjà votre besoin. |
| **Point d’entrée principal** | `python -m loraflexsim.run --output final/data/...`, puis `examples/analyse_resultats.py` ou les scripts de `final/plots/`. |
| **Sorties produites** | CSV dans `final/data/`, figures dans `final/figures/`, scripts/scénarios dans `final/scenarios/` et plots historiques dans `final/plots/`. |
| **Documentation détaillée** | `docs/advanced_workflows.md` explique le positionnement de `final/`, et ce README détaille le flux minimal ci-dessous. |

> [!WARNING]
> **Archive / reproduction** : ce dossier conserve un flux historique de génération de CSV et de figures.

Ce dossier regroupe un flux de travail **reproductible** pour générer des scénarios, stocker les CSV et centraliser les figures produites par LoRaFlexSim.

## Documentation détaillée

### Prérequis

#### Politique locale alignée avec le README principal

- **OS documenté en priorité : Windows 11**.
- **Shell documenté : PowerShell**.
- **Répertoire d’exécution : racine du dépôt**.
- **Version Python recommandée : 3.11**.
- **Support packaging : Python 3.11 à 3.12**.
- **Installation standard recommandée :** `python -m pip install -e . --no-build-isolation` après activation du venv.
- **`PYTHONPATH=src` n’est pas requis** pour ce flux standard ; il ne concerne que certains contournements offline/fallback.

#### Installation recommandée

Depuis la **racine du dépôt** dans **PowerShell** :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

> Si PowerShell bloque l’activation, utilisez : `powershell -ExecutionPolicy Bypass -File .\.venv\Scripts\Activate.ps1`.

### Scénario minimal

Depuis la **racine du dépôt** dans **PowerShell**, lancez une simulation qui écrit un CSV dans `final/data/` :

```powershell
python -m loraflexsim.run --nodes 30 --gateways 1 --mode random --interval 10 --steps 100 --output final/data/simulation.csv
```

### Plots

L’exemple suivant lit un ou plusieurs CSV et génère une figure de PDR moyenne dans `final/figures/`.

```powershell
python examples/analyse_resultats.py final/data/simulation.csv --output-dir final/figures --basename pdr_by_nodes
```

### Emplacement des sorties

- CSV de simulation : `final/data/`
- Figures : `final/figures/`
- Scénarios personnalisés : `final/scenarios/`
- Graphiques complémentaires : `final/plots/`

### Ajuster les paramètres clés

- **Période d’émission** : ajustez `--interval` (en secondes). Exemple : `--interval 60`.
- **Rayon / taille de zone** : pour des scénarios plus larges, privilégiez les presets longue portée (`--long-range-demo`) ou l’auto-calibrage (`--long-range-auto <surface_km2> [distance_km]`). Pour un contrôle fin de la zone (mètres), créez un script Python qui instancie `Simulator(area_size=...)` et placez-le dans `final/scenarios/`.
- **Taille de paquet** : la CLI `loraflexsim.run` utilise la valeur par défaut, mais vous pouvez la surcharger en Python via `Simulator(payload_size_bytes=...)`.

### Exemple de script minimal (à placer dans `final/scenarios/`)

```python
from loraflexsim.launcher.simulator import Simulator

sim = Simulator(
    nodes=30,
    gateways=1,
    area_size=2000.0,
    payload_size_bytes=40,
    interval=60.0,
    steps=600,
)
metrics = sim.run()
print(metrics)
```

### Lien direct vers la doc détaillée

- `docs/advanced_workflows.md`
