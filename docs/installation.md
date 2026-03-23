# Installation et compatibilité plateforme

Ce guide documente le parcours canonique de LoRaFlexSim.

## Décision officielle

La surface publique du simulateur est désormais :

- **dashboard** : `panel serve loraflexsim/launcher/dashboard.py --show`
- **CLI officielle** : `loraflexsim ...`

Les commandes `mobilesfrdth ...` et `python -m loraflexsim.run ...` restent disponibles pour compatibilité ou usage bas niveau, mais **ne sont plus le parcours recommandé**.

## Matrice de compatibilité

| Surface | Windows 11 | Linux | macOS |
| --- | --- | --- | --- |
| Installation editable | **prioritaire** | documentée | documentée |
| CLI `loraflexsim` | **prioritaire** | documentée | documentée |
| Wrapper dépôt `scripts/loraflexsim.*` | **oui** | **oui** | **oui** |
| Dashboard Panel | **prioritaire** | documenté | documenté |
| `python -m loraflexsim.run` | historique | historique | historique |

## Installation recommandée

### Windows 11 / PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

### Linux / macOS / bash

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-build-isolation
```

## Dépendances utiles selon le flux

- **CLI `loraflexsim` installée** : `python -m pip install -e . --no-build-isolation`
- **Dashboard** : runtime complet + `panel`, `plotly`, `numpy`, `pandas`
- **Fallback dépôt / offline** : `matplotlib` et `PyYAML` restent le minimum pratique pour la chaîne CLI existante

## Lancer la CLI officielle

### Après installation editable

```powershell
loraflexsim --help
loraflexsim presets --list
loraflexsim run --preset paper_fast --out runs/quickstart
```

Sous Linux/macOS, les mêmes commandes s’exécutent en bash/zsh.

### Fallback dépôt

#### Windows 11

```powershell
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 presets --list
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 run --preset paper_fast --out runs/quickstart
```

#### Linux / macOS

```bash
./scripts/loraflexsim.sh --help
./scripts/loraflexsim.sh presets --list
./scripts/loraflexsim.sh run --preset paper_fast --out runs/quickstart
```

### Compatibilité legacy

Ces formes restent valides si vous maintenez un ancien script :

```powershell
mobilesfrdth --help
python -m mobilesfrdth --help
python -m loraflexsim.run --help
```

Mais, pour la documentation utilisateur, **préférez désormais `loraflexsim`**.

## Lancer le dashboard

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

Même commande sous bash/zsh.

## Scripts recommandés

| Script | Rôle | Plateformes |
| --- | --- | --- |
| `scripts/bootstrap_windows.ps1` | bootstrap Windows 11 | Windows 11 |
| `scripts/bootstrap_unix.sh` | bootstrap Unix | Linux, macOS |
| `scripts/loraflexsim.ps1` | wrapper dépôt canonique | Windows 11 |
| `scripts/loraflexsim.sh` | wrapper dépôt canonique | Linux, macOS |
| `scripts/mobilesfrdth.ps1` | wrapper legacy | Windows 11 |
| `scripts/mobilesfrdth.sh` | wrapper legacy | Linux, macOS |

## Limitations connues

- `panel serve ... --show` dépend de la capacité du système à ouvrir un navigateur par défaut.
- `python -m loraflexsim.run` expose un niveau plus bas que la CLI officielle et n’offre pas le parcours `run -> aggregate -> plots -> validate` documenté pour la communauté.
- Le nom de package interne reste `mobilesfrdth`, ce qui explique la présence de commandes de compatibilité.

## Parcours recommandé sans ambiguïté

### Windows 11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
loraflexsim --help
panel serve loraflexsim/launcher/dashboard.py --show
```

### Linux / macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-build-isolation
loraflexsim --help
panel serve loraflexsim/launcher/dashboard.py --show
```
