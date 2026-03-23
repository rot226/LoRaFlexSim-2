# LoRaFlexSim 1.0.1

LoRaFlexSim est un simulateur LoRa/LoRaWAN en Python avec deux surfaces publiques désormais **canoniques** :

- le **dashboard Panel** pour l’exploration visuelle ;
- la **CLI officielle `loraflexsim`** pour les campagnes reproductibles.

L’ancienne CLI `mobilesfrdth` reste disponible uniquement comme **alias de compatibilité** et ne doit plus être présentée comme parcours recommandé.

## Installer

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

## Lancer le dashboard

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

La commande est identique sous bash/zsh.

## Lancer la CLI officielle

```powershell
loraflexsim --help
loraflexsim presets --list
loraflexsim run --preset paper_fast --out runs/quickstart
```

### Fallback dépôt si l’entrypoint console n’est pas disponible

- **Windows 11** : `powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help`
- **Linux / macOS** : `./scripts/loraflexsim.sh --help`
- **Fallback Python direct** : `python -m mobilesfrdth --help`

## Décision de surface publique

La surface publique du simulateur est fixée explicitement comme suit :

1. **Dashboard public** : `panel serve loraflexsim/launcher/dashboard.py --show`
2. **CLI publique officielle** : `loraflexsim ...`
3. **Entrées non canoniques mais conservées** :
   - `python -m loraflexsim.run` pour le moteur historique ;
   - `mobilesfrdth` pour compatibilité avec des scripts existants.

Autrement dit :

- un **nouvel utilisateur** doit commencer par le dashboard ou par `loraflexsim` ;
- `python -m loraflexsim.run` est un chemin **historique / bas niveau** ;
- `mobilesfrdth` n’est plus la CLI mise en avant dans la documentation.

## Premier workflow CLI recommandé

```powershell
loraflexsim run --preset paper_fast --out runs/quickstart
loraflexsim aggregate --results runs/quickstart --out runs/quickstart
loraflexsim plots --aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory
loraflexsim validate --aggregates-dir runs/quickstart/aggregates
```

Sorties attendues :

- `runs/quickstart/results/`
- `runs/quickstart/aggregates/`
- `runs/quickstart/plots/`

## Où aller ensuite ?

- `docs/installation.md` : installation, compatibilité plateforme et fallbacks.
- `docs/user_guide_dashboard.md` : démarrage guidé du dashboard.
- `docs/user_guide_cli.md` : guide complet de la CLI officielle `loraflexsim`.
- `docs/user_entrypoints_inventory.md` : inventaire détaillé des entrées utilisateur.
- `docs/repository_map.md` : carte de gouvernance documentaire du dépôt.
- `loraflexsim/README.md` : rôle du cœur historique `loraflexsim/`.

## Structure rapide du dépôt

| Dossier | Rôle | Statut |
| --- | --- | --- |
| `loraflexsim/` | cœur historique du simulateur et dashboard | officiel pour le moteur et l’UI |
| `src/mobilesfrdth/` | implémentation technique de la CLI packagée | officiel comme backend de la commande `loraflexsim` |
| `docs/` | documentation utilisateur et technique | officiel |
| `scripts/` | wrappers et automatisation locale | officiel |
| `final/`, `pretest_campagne/` | reproduction et workflows historiques | historique / recherche |
| `sfrd/`, `qos_cli/` | CLIs spécialisées | avancé / non canonique |

## Compatibilité résumée

| Surface | Windows 11 | Linux | macOS |
| --- | --- | --- | --- |
| CLI `loraflexsim` | documentée et prioritaire | documentée | documentée |
| Dashboard Panel | documenté et prioritaire | documenté | documenté |
| `python -m loraflexsim.run` | support historique | support historique | support historique |

## Notes de compatibilité

- L’installation editable reste la méthode recommandée.
- Le packaging du dépôt cible **Python 3.11 à 3.12**.
- Le nom interne du package packagé reste `mobilesfrdth`, mais la **surface publique documentée** est désormais `loraflexsim`.
- Si `panel serve ... --show` n’ouvre pas automatiquement le navigateur, copiez l’URL affichée dans votre navigateur.
