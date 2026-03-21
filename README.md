# LoRaFlexSim 1.0.1 : accueil communauté

LoRaFlexSim est un simulateur LoRa/LoRaWAN en Python pour explorer des scénarios radio, de mobilité et d'ADR, via un dashboard interactif ou une CLI reproductible.

## Démarrage rapide Windows 11

Depuis la racine du dépôt dans **PowerShell** :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
mobilesfrdth --help
panel serve loraflexsim/launcher/dashboard.py --show
```

> [!IMPORTANT]
> **Entrées recommandées pour un premier usage**
> - **Dashboard** : `panel serve loraflexsim/launcher/dashboard.py --show`
> - **CLI communauté** : `mobilesfrdth --help`
>
> Les autres interfaces présentes dans le dépôt sont conservées pour des usages avancés, historiques ou de reproduction.

## Arborescence documentaire recommandée

- `README.md` : point d’entrée communauté.
- `docs/user_guide_dashboard.md` : premier usage du dashboard.
- `docs/user_guide_cli.md` : premier usage de la CLI `mobilesfrdth`.
- `docs/advanced_workflows.md` : workflows complets, génération de figures et pipelines spécialisés.
- `docs/archive_or_research/` : documentation historique, campagnes de reproduction, comparatifs et archives.

## Par où commencer ?

### 1. Découvrir le dashboard

Le dashboard est la meilleure porte d’entrée si vous voulez lancer un premier essai sans mémoriser beaucoup d’options.

➡ Voir `docs/user_guide_dashboard.md`.

### 2. Utiliser la CLI officielle

La CLI `mobilesfrdth` couvre le flux stable recommandé pour les campagnes reproductibles.

➡ Voir `docs/user_guide_cli.md`.

### 3. Aller plus loin

Pour les workflows complets, la génération/export de figures, les pipelines spécialisés et les interfaces secondaires, consultez :

➡ `docs/advanced_workflows.md`

### 4. Reproduction, campagnes historiques et recherche

Les contenus de reproduction et les campagnes héritées sont maintenant regroupés sous :

➡ `docs/archive_or_research/`

## Documentation complémentaire

- Scénarios et usages : `docs/usage_scenarios.md`
- Validation et plan de test : `docs/VALIDATION.md`, `docs/test_plan.md`, `docs/validation_status.md`
- Modèle radio / hypothèses : `docs/lorawan_features.md`, `docs/equations_flora.md`, `docs/snir_assumptions.md`
- ADR, énergie, longue portée, obstacles, QoS : `docs/adr_protocols.md`, `docs/energy_profiles.md`, `docs/long_range.md`, `docs/obstacle_loss.md`, `docs/qos_cluster_bench_report.md`, `docs/qos_cluster_validation_pipeline.md`
- Reproduction FLoRa et extension du dashboard : `docs/reproduction_flora.md`, `docs/extension_guide.md`

## Vérification avant contribution

Depuis la racine du dépôt :

```bash
make validate
```

Sous Windows, utilisez un terminal disposant de `make` (Git Bash, WSL ou équivalent).
