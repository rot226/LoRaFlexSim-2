# `sfrd/`

## En 30 secondes

| Rubrique | Réponse rapide |
| --- | --- |
| **À quoi sert ce dossier ?** | Fournir la CLI SFRD avancée/spécialisée pour des campagnes ciblées, de la calibration UCB et des validations dédiées hors du flux standard. |
| **Quand l’utiliser ?** | Quand vous travaillez sur un pipeline SFRD avancé déjà existant, avec des scripts de `sfrd/cli/` ou une logique d’agrégation/validation spécifique. |
| **Quand ne pas l’utiliser ?** | Ne l’utilisez pas pour un premier contact avec le projet ni pour une campagne standard : la voie recommandée reste `mobilesfrdth`. |
| **Point d’entrée du dossier** | Les commandes Python de `sfrd.cli`, par exemple `python -m sfrd.cli.run_campaign` ou `python -m sfrd.cli.validate_outputs`. |
| **Statut de gouvernance** | CLI avancée / spécialisée ; pas de concurrence avec la CLI officielle recommandée `mobilesfrdth`. |
| **Sorties produites** | Des sorties de campagne SFRD, des journaux, des validations et des agrégations dépendant du workflow choisi. |
| **Documentation détaillée** | `docs/advanced_workflows.md` décrit quand basculer vers `sfrd/` et les principaux cas d’usage avancés. |

CLI avancée / spécialisée.

> [!TIP]
> **Non nécessaire pour un premier usage** — cette CLI spécialisée est conservée pour des campagnes SFRD avancées et distinctes de l’interface communauté `mobilesfrdth`.

## Positionnement des points d’entrée

- **Point d’entrée officiel recommandé** : `mobilesfrdth`
- **Points d’entrée avancés / spécialisés** : `sfrd`
- **Flux historiques / reproduction** : `final`, `mobile-sfrd`
- **Archives / anciens pipelines** : tout dossier déplacé sous l’espace d’archives

## Documentation détaillée

### Objectif du dossier

Ce dossier sert surtout de point de redirection vers la documentation SFRD maintenue ailleurs dans le dépôt.

### Prérequis

- **OS documenté en priorité : Windows 11**.
- **Shell documenté : PowerShell**.
- **Répertoire d’exécution : racine du dépôt**.
- **Version Python recommandée : 3.11**.
- **Support packaging : Python 3.11 à 3.12**.
- **Installation standard recommandée :** `python -m pip install -e . --no-build-isolation` après activation du venv.
- **`PYTHONPATH=src` n’est pas requis** pour l’usage standard documenté.

### Scénario minimal

Pour un premier repérage, ouvrez la documentation consolidée avant toute exécution spécifique.

### Commandes typiques

Aucune commande unique n’est imposée dans ce README. Les points d’entrée les plus probables sont :

- `python -m sfrd.cli.run_campaign`
- `python -m sfrd.cli.plot_campaign`
- `python -m sfrd.cli.validate_outputs`
- `python -m sfrd.cli.calibrate_ucb`

### Sorties

Les sorties dépendent du workflow SFRD choisi ; ce dossier ne normalise pas un seul format de résultats.

### Lien direct vers la doc détaillée

- `docs/advanced_workflows.md`
