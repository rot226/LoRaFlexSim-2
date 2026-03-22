# Installation et compatibilité plateforme

Ce document explique **quelle plateforme est supportée**, **quels scripts utiliser** et **quelles limitations connaître** avant de lancer LoRaFlexSim.

Le **point d’entrée CLI recommandé** reste `mobilesfrdth` sur toutes les plateformes.

## Matrice de compatibilité plateforme

| Surface | Windows 11 | Linux | macOS |
| --- | --- | --- | --- |
| Statut global | **Support documenté principal** | **Support visé / partiel** | **Support visé / partiel** |
| Installation Python 3.11 / 3.12 | **Documentée et prioritaire** | **Documentée et visée** | **Documentée et visée** |
| CLI `mobilesfrdth` via installation editable | **Validée / recommandée** | **Visée / fallback documenté** | **Visée / fallback documenté** |
| CLI `mobilesfrdth` via wrapper dépôt | **Validée** avec `scripts/mobilesfrdth.ps1` | **Documentée** avec `scripts/mobilesfrdth.sh` | **Documentée** avec `scripts/mobilesfrdth.sh` |
| Dashboard Panel | **Documenté en priorité** | **Visé** | **Visé** |
| Scripts Bash | **Possibles via Git Bash/WSL mais non prioritaires** | **Oui** | **Oui** |
| Scripts PowerShell | **Oui** | **Oui si PowerShell 7 est installé** | **Oui si PowerShell 7 est installé** |
| Ouverture automatique de dossier / navigateur | **Partielle** selon la politique locale Windows | **Partielle** selon présence de `xdg-open` | **Partielle** selon présence de `open` |
| Build natif FLoRa (`make`) | **Secondaire** | **Visé** | **Visé** |

## Recommandation simple par plateforme

- **Windows 11** : suivez en priorité les commandes **PowerShell** du dépôt.
- **Linux/macOS** : utilisez en priorité les commandes **bash/zsh** ci-dessous et les wrappers `*.sh` ajoutés au dépôt.
- Si l’installation editable échoue sur n’importe quelle plateforme, utilisez le **fallback `python -m mobilesfrdth`** ou le wrapper dépôt correspondant.

## Python 3.11 / 3.12

Le packaging du projet déclare `requires-python = ">=3.11,<3.13"`. En pratique, la cible documentée est donc **Python 3.11 ou 3.12**.

### Windows 11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

Si Python 3.11 n’est pas disponible mais que Python 3.12 l’est :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

### Linux

Avec Python 3.11 :

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-build-isolation
```

Avec Python 3.12 :

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-build-isolation
```

### macOS

Avec Python 3.11 :

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-build-isolation
```

Avec Python 3.12 :

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-build-isolation
```

### Bootstrap automatisé côté dépôt

- **Windows 11 / PowerShell** : `./scripts/bootstrap_windows.ps1`
- **Linux/macOS / bash** : `./scripts/bootstrap_unix.sh`

Le script Unix privilégie `python3.11`, puis `python3.12`, et n’accepte `python3`/`python` que s’ils pointent eux-mêmes vers Python 3.11 ou 3.12.

## Dépendances réellement requises selon le flux

- **Installation editable recommandée** : `python -m pip install -e . --no-build-isolation` installe le **runtime complet documenté** (CLI `mobilesfrdth`, dashboard Panel, API FastAPI/WebSocket, lecture YAML).
- **Flux standard `mobilesfrdth` (`run -> aggregate -> plots -> validate`) sans installation editable** : les dépendances minimales réellement requises sont **`matplotlib`** et **`PyYAML`**.
- **Dashboard Panel** : ajoutez **`panel`**, **`plotly`**, **`numpy`** et **`pandas`**.
- **API web** : ajoutez **`fastapi`** et **`uvicorn`**.
- **Compatibilité YAML** : le module importé est `yaml`, fourni par le paquet **PyYAML**.

Le fichier `requirements.txt` reste aligné sur le **runtime complet local**. Il installe donc plus que le strict minimum du flux CLI/offline, mais il ne laisse pas de dépendance manquante pour le dashboard ou l'API.

## Lancer la CLI `mobilesfrdth`

### Méthode recommandée après installation editable

Une fois l’environnement installé et activé :

```bash
mobilesfrdth --help
mobilesfrdth presets --list
mobilesfrdth run --preset paper_fast --out runs/quickstart
```

Sous Windows 11, les mêmes commandes s’exécutent dans PowerShell.

### Fallback sans installation editable

Si l’entrypoint console n’est pas installé ou si vous travaillez en mode dépôt :

#### Linux / macOS

```bash
./scripts/mobilesfrdth.sh --help
./scripts/mobilesfrdth.sh presets --list
./scripts/mobilesfrdth.sh run --preset paper_fast --out runs/quickstart
```

Équivalent direct :

```bash
PYTHONPATH=src python -m mobilesfrdth --help
```

#### Windows 11

```powershell
powershell -ExecutionPolicy Bypass -File scripts/mobilesfrdth.ps1 --help
```

Équivalent direct :

```powershell
$env:PYTHONPATH='src'
python -m mobilesfrdth --help
```

## Lancer le dashboard

Le dashboard recommandé est servi par Panel.

### Toutes plateformes

Après activation de l’environnement :

```bash
panel serve loraflexsim/launcher/dashboard.py --show
```

### Windows 11

Commande identique en PowerShell :

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

### Linux / macOS

Commande identique en bash/zsh :

```bash
panel serve loraflexsim/launcher/dashboard.py --show
```

Si `--show` n’ouvre pas automatiquement le navigateur, recopiez simplement l’URL affichée par Panel dans votre navigateur.

## Scripts disponibles en Bash

Les scripts suivants sont prévus pour être lancés depuis **bash/zsh** à la racine du dépôt.

| Script | Usage | Plateformes visées |
| --- | --- | --- |
| `scripts/bootstrap_unix.sh` | Crée `.venv`, active l’environnement, tente `pip install -e . --no-build-isolation`, puis affiche la commande CLI à utiliser. | Linux, macOS |
| `scripts/mobilesfrdth.sh` | Wrapper dépôt vers `python -m mobilesfrdth` avec `PYTHONPATH=src`. | Linux, macOS |
| `scripts/run_campaign_profiles.sh` | Lance des profils de campagne `mobilesfrdth` (`smoke`, `core_article`, `full_article`). | Linux, macOS |
| `scripts/run_grid.sh` | Exécute `run`, `aggregate`, puis `plots` avec des chaînes d’arguments bash. | Linux, macOS |
| `scripts/run_all_fast.sh` | Orchestrateur rapide de scénarios représentatifs. | Linux, macOS |
| `scripts/run_ci_pipeline.sh` | Pipeline CI/bash plus large. | Linux, macOS |
| `scripts/build_flora_cpp.sh` | Compile la bibliothèque native FLoRa avec `make`. | Linux, macOS |

### Exemples Bash prêts à l’emploi

```bash
./scripts/bootstrap_unix.sh
source .venv/bin/activate
./scripts/mobilesfrdth.sh --help
./scripts/run_campaign_profiles.sh smoke runs/campaign_profiles
./scripts/run_grid.sh "--preset paper_fast --out runs/quickstart" "--results runs/quickstart --out runs/quickstart" "--aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory"
```

## Scripts disponibles en PowerShell

Les scripts suivants sont les scripts Windows 11 documentés en priorité.

| Script | Usage | Plateformes visées |
| --- | --- | --- |
| `scripts/bootstrap_windows.ps1` | Crée `.venv`, tente l’installation editable, puis affiche la bonne commande de lancement. | Windows 11 |
| `scripts/mobilesfrdth.ps1` | Wrapper dépôt vers `python -m mobilesfrdth` avec `PYTHONPATH=src`. | Windows 11 |
| `scripts/run_grid.ps1` | Exécute `run`, `aggregate`, puis `plots`. | Windows 11 |
| `scripts/run_campaign_profiles.ps1` | Lance des profils de campagne `mobilesfrdth`. | Windows 11 |
| `scripts/run_step1_matrix_windows.ps1` | Pipeline Windows dédié à la matrice Step 1. | Windows 11 |

## Limitations connues

### Ouverture automatique du navigateur ou d’un dossier

- Le dashboard lancé avec `panel serve ... --show` dépend de la capacité du système à ouvrir un navigateur par défaut.
- L’export dashboard tente une ouverture automatique du dossier de sortie via `open` sur macOS ou `xdg-open` sur Linux.
- Si `xdg-open` ou `open` est absent, rien n’empêche la génération des résultats, mais l’ouverture automatique peut échouer silencieusement ou ne rien faire.

### Dépendances GUI

- Le dashboard nécessite les dépendances Python graphiques déclarées dans le projet, notamment `panel`.
- Sur des environnements serveur, CI ou SSH sans navigateur local, le dashboard peut être servi mais **pas affiché automatiquement**.

### `make` et build natif FLoRa

- `scripts/build_flora_cpp.sh` suppose la disponibilité de `make`.
- Sous Linux/macOS, ce script est naturel si l’outillage de compilation est installé.
- Sous Windows 11, ce flux natif n’est **pas** le parcours principal documenté.

### Bash vs PowerShell

- Les scripts `*.ps1` sont la référence Windows 11.
- Les scripts `*.sh` ajoutés ici sont les équivalents à utiliser sur Linux/macOS ; il n’est pas nécessaire de retranscrire mentalement les commandes PowerShell.
- Sous Linux/macOS, si vous préférez PowerShell 7, les scripts `*.ps1` restent souvent utilisables, mais **ce n’est pas la voie documentée principale**.

### Fallback `PYTHONPATH=src`

- Le fallback `PYTHONPATH=src python -m mobilesfrdth ...` est utile quand l’installation editable échoue.
- Ce mode est documenté et assumé, mais l’expérience la plus propre reste l’entrypoint `mobilesfrdth` installé via `pip install -e . --no-build-isolation`.

## Parcours recommandé sans ambiguïté

### Windows 11

```powershell
./scripts/bootstrap_windows.ps1
.\.venv\Scripts\Activate.ps1
mobilesfrdth --help
panel serve loraflexsim/launcher/dashboard.py --show
```

### Linux

```bash
./scripts/bootstrap_unix.sh
source .venv/bin/activate
./scripts/mobilesfrdth.sh --help
panel serve loraflexsim/launcher/dashboard.py --show
```

### macOS

```bash
./scripts/bootstrap_unix.sh
source .venv/bin/activate
./scripts/mobilesfrdth.sh --help
panel serve loraflexsim/launcher/dashboard.py --show
```

## Références croisées

- Vue d’ensemble : `README.md`
- Guide CLI : `docs/user_guide_cli.md`
- Guide dashboard : `docs/user_guide_dashboard.md`
- Workflows avancés : `docs/advanced_workflows.md`
