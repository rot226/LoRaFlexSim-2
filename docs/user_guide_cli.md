# Guide utilisateur — CLI officielle `loraflexsim`

La CLI officielle mise en avant pour la communauté est désormais **`loraflexsim`**.

Elle correspond au parcours canonique pour :

- lancer une campagne ;
- agréger les résultats ;
- générer des figures ;
- valider les agrégats.

L’ancien nom `mobilesfrdth` reste disponible comme **alias de compatibilité**, mais n’est plus la surface publique recommandée.

## Positionnement des points d’entrée

- **CLI officielle recommandée** : `loraflexsim`
- **Dashboard officiel** : `panel serve loraflexsim/launcher/dashboard.py --show`
- **CLI technique / historique** : `python -m loraflexsim.run`
- **Pipelines spécialisés / recherche** : `qos_cli/`, `pretest_campagne/`, `docs/archive_or_research/`

Si vous ne savez pas quelle commande utiliser, **choisissez `loraflexsim`**.

## Vérifier l’installation

### Windows 11 / PowerShell

```powershell
loraflexsim --help
```

### Linux / macOS / bash

```bash
loraflexsim --help
```

## Fallbacks si l’entrypoint console n’est pas disponible

### Windows 11

```powershell
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help
python -m mobilesfrdth --help
```

### Linux / macOS

```bash
./scripts/loraflexsim.sh --help
python -m mobilesfrdth --help
```

## Workflow minimal recommandé

### 1. Lister les presets

```powershell
loraflexsim presets --list
```

### 2. Lancer une campagne

```powershell
loraflexsim run --preset paper_fast --out runs/quickstart
```

Alternative explicite :

```powershell
loraflexsim run --config experiments/default.yaml --out runs/quickstart --profile smoke
```

### 3. Agréger les résultats

```powershell
loraflexsim aggregate --results runs/quickstart --out runs/quickstart
```

### 4. Générer les figures

```powershell
loraflexsim plots --aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory
```

### 5. Valider les agrégats

```powershell
loraflexsim validate --aggregates-dir runs/quickstart/aggregates
```

## Rôle de chaque étape

- `presets` : liste les presets disponibles ;
- `run` : exécute la campagne ;
- `aggregate` : consolide les résultats ;
- `plots` : génère les figures ;
- `validate` : vérifie la cohérence des agrégats.

## Quand utiliser `python -m loraflexsim.run` ?

Utilisez `python -m loraflexsim.run` seulement si vous avez un besoin **historique**, **bas niveau** ou **de débogage moteur**.

Pour la documentation utilisateur générale, le chemin canonique reste **`loraflexsim`**.

## Compatibilité legacy

Les commandes suivantes restent valides, mais doivent être lues comme des chemins de compatibilité :

```powershell
mobilesfrdth --help
python -m mobilesfrdth --help
```

Le backend packagé de compatibilité vit désormais dans `mobilesfrdth/`, tandis que la surface publique documentée reste `loraflexsim`.

## Interfaces secondaires

- `docs/user_guide_dashboard.md` : dashboard officiel ;
- `docs/archive_or_research/sfrd_legacy.md` : archive documentaire du pipeline SFRD retiré ;
- `qos_cli/README.md` : CLI QoS spécialisée ;
- `docs/archive_or_research/final_legacy.md` : archive documentaire des anciens exports CSV/figures ;
- `pretest_campagne/` : campagnes de recherche et de reproduction.
