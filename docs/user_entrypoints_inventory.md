# Inventaire des scripts d’entrée utilisateur

Ce document recense les points d’entrée encore visibles dans le dépôt et précise leur statut après la décision de surface publique.

## Décision canonique

- **Dashboard public** : `panel serve loraflexsim/launcher/dashboard.py --show`
- **CLI publique officielle** : `loraflexsim ...`
- **Entrées legacy / techniques** : `mobilesfrdth ...`, `python -m loraflexsim.run ...`

## Dépendances de base

| Famille | Dépendances minimales documentées |
| --- | --- |
| CLI officielle `loraflexsim` | runtime complet via `python -m pip install -e . --no-build-isolation` |
| Wrapper dépôt `scripts/loraflexsim.*` | Python 3.11/3.12 ; `matplotlib`, `PyYAML` au minimum en fallback |
| Dashboard | runtime complet + `panel`, `plotly`, `numpy`, `pandas` |
| Entrées historiques / recherche | variable selon le dossier |

## 1. Entrées publiques à privilégier

| Entrée | Statut | Shell cible | Plateformes |
| --- | --- | --- | --- |
| `loraflexsim` | **CLI officielle** | PowerShell, bash, zsh | Windows 11, Linux, macOS |
| `scripts/loraflexsim.ps1` | **wrapper dépôt officiel** | PowerShell | Windows 11 |
| `scripts/loraflexsim.sh` | **wrapper dépôt officiel** | bash | Linux, macOS |
| `panel serve loraflexsim/launcher/dashboard.py --show` | **dashboard officiel** | PowerShell, bash, zsh | Windows 11, Linux, macOS |

## 2. Entrées conservées mais non canoniques

| Entrée | Statut | Quand l’utiliser |
| --- | --- | --- |
| `mobilesfrdth` | alias legacy | maintenance d’anciens scripts ou habitudes locales |
| `python -m mobilesfrdth` | fallback technique | environnement où l’entrypoint console n’est pas installé |
| `scripts/mobilesfrdth.ps1` / `scripts/mobilesfrdth.sh` | wrappers legacy | compatibilité dépôt |
| `python -m loraflexsim.run` | moteur historique bas niveau | tests ciblés, débogage ou documentation historique |

## 3. Dossier `scripts/`

### Wrappers et bootstrap

| Script | Statut | Plateformes | Commentaire |
| --- | --- | --- | --- |
| `scripts/bootstrap_windows.ps1` | recommandé | Windows 11 | prépare l’environnement local |
| `scripts/bootstrap_unix.sh` | recommandé | Linux, macOS | prépare l’environnement local |
| `scripts/loraflexsim.ps1` | canonique | Windows 11 | wrapper dépôt vers `python -m mobilesfrdth` |
| `scripts/loraflexsim.sh` | canonique | Linux, macOS | wrapper dépôt vers `python -m mobilesfrdth` |
| `scripts/mobilesfrdth.ps1` | legacy | Windows 11 | conserve l’ancien nom public |
| `scripts/mobilesfrdth.sh` | legacy | Linux, macOS | conserve l’ancien nom public |

### Scripts spécialisés

Les autres scripts de `scripts/` restent des outils d’automatisation, de validation, de tracé ou de reproduction. Ils ne définissent pas la surface publique de premier niveau.

## 4. Dossiers historiques et spécialisés

| Zone | Statut | Remarque |
| --- | --- | --- |
| `docs/archive_or_research/final_legacy.md` | archive documentaire | description des anciens pipelines d’export CSV/figures |
| `pretest_campagne/` | recherche / reproduction | campagnes scientifiques et archives |
| `docs/archive_or_research/sfrd_legacy.md` | archive documentaire | description du pipeline SFRD retiré du dépôt exécutable |
| `qos_cli/` | spécialisé | interface experte |

## 5. Recommandation courte

- **Nouveau point d’entrée CLI à documenter** : `loraflexsim`
- **Nouveau point d’entrée visuel à documenter** : le dashboard Panel
- **À éviter comme message public** : « CLI officielle recommandée `mobilesfrdth` »
- **À garder comme note de compatibilité** : `mobilesfrdth` reste un alias legacy
