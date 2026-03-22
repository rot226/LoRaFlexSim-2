# LoRaFlexSim 1.0.1 : accueil communauté

LoRaFlexSim est un simulateur LoRa/LoRaWAN en Python pour explorer des scénarios radio, de mobilité et d'ADR, via un dashboard interactif ou une CLI reproductible.

Ce dépôt est destiné à la communauté : le simulateur peut être utilisé librement, la documentation privilégie une prise en main rapide, et le parcours de lecture distingue clairement l’usage standard recommandé des workflows avancés, de recherche ou de reproduction.

## Orientation rapide des points d’entrée

Pour éviter toute hésitation entre plusieurs CLI ou dossiers :

- **Point d’entrée officiel recommandé** : `mobilesfrdth`
- **Points d’entrée avancés / spécialisés** : `sfrd`
- **Flux historiques / reproduction** : `final`, `mobile-sfrd`
- **Archives / anciens pipelines** : tout dossier déplacé sous l’espace d’archives

En pratique, **si vous débutez ou si vous lancez une nouvelle campagne, utilisez `mobilesfrdth`**. Les autres entrées ne doivent être utilisées que si vous savez déjà que votre besoin relève d’un workflow spécialisé, historique ou archivé.

## Politique d’installation et d’exécution

### Compatibilité plateforme

| Surface | Windows 11 | Linux | macOS |
| --- | --- | --- | --- |
| Statut global | **Support documenté principal** | **Support visé / partiel** | **Support visé / partiel** |
| Installation Python 3.11 / 3.12 | **Documentée et prioritaire** | **Documentée et visée** | **Documentée et visée** |
| CLI `mobilesfrdth` | **Validée / recommandée** | **Visée / fallback documenté** | **Visée / fallback documenté** |
| Dashboard Panel | **Documenté en priorité** | **Visé** | **Visé** |
| Scripts Bash | **Secondaires** | **Oui** | **Oui** |
| Scripts PowerShell | **Oui** | **Oui si PowerShell 7 est installé** | **Oui si PowerShell 7 est installé** |

- **Plateforme documentée en priorité : Windows 11**.
- **Linux et macOS sont documentés explicitement** via `docs/installation.md` et les wrappers Bash `scripts/bootstrap_unix.sh`, `scripts/mobilesfrdth.sh`, `scripts/run_campaign_profiles.sh` et `scripts/run_grid.sh`.
- **`cmd.exe` n’est pas la cible documentaire principale**.

### Version Python

- **Version recommandée : Python 3.11**.
- **Versions prises en charge par le packaging : Python 3.11 à 3.12**.
- Sous Windows, utilisez de préférence **`py -3.11`**.
- Sous Linux/macOS, utilisez de préférence **`python3.11`** ou **`python3.12`**.

### Dépendances réellement utiles selon le flux

- **Installation editable recommandée** : `python -m pip install -e . --no-build-isolation` installe le **runtime complet documenté** du dépôt (CLI `mobilesfrdth`, dashboard Panel, API FastAPI et lecture YAML).
- **Flux standard `mobilesfrdth` (`run -> aggregate -> plots -> validate`) en mode dépôt/offline** : les dépendances minimales réellement requises sont **`matplotlib`** et **`PyYAML`**.
- **Dashboard** : ajoute explicitement **`panel`**, **`plotly`**, **`numpy`** et **`pandas`**.
- **API web** : ajoute **`fastapi`** et **`uvicorn`**.
- **Compatibilité YAML** : le module Python importé est `yaml`, fourni par le paquet **PyYAML**.

### Méthodes d’installation recommandées

#### Windows 11 / PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

#### Linux / macOS / bash

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-build-isolation
```

Wrappers dépôt disponibles :

- **Windows 11** : `./scripts/bootstrap_windows.ps1`
- **Linux / macOS** : `./scripts/bootstrap_unix.sh`

L'installation editable canonique expose désormais **une seule distribution Python et une seule arborescence source pour `mobilesfrdth`** : `pyproject.toml` pointe sur `src/mobilesfrdth/`, et l'ancien doublon `mobile-sfrd_th/src/mobilesfrdth/` ne doit plus être utilisé.

### Méthode fallback

> [!IMPORTANT]
> **Mode fallback à utiliser seulement si l’installation editable échoue**.

#### Windows 11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install matplotlib PyYAML
powershell -ExecutionPolicy Bypass -File scripts/windows/run_offline.ps1
```

#### Linux / macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
./scripts/mobilesfrdth.sh --help
```

Dans ce mode seulement, certains scripts positionnent **`PYTHONPATH=src`** automatiquement. **Vous n’avez pas besoin de définir `PYTHONPATH=src` pour l’installation standard.**

➡ Voir `docs/installation.md` pour la matrice complète, les scripts par shell et les limitations connues.

## Démarrage rapide Windows 11

Depuis la **racine du dépôt** dans **PowerShell** :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
mobilesfrdth --help
mobilesfrdth presets --list
panel serve loraflexsim/launcher/dashboard.py --show
```

> [!IMPORTANT]
> **Entrées recommandées pour un premier usage**
> - **Dashboard** : `panel serve loraflexsim/launcher/dashboard.py --show`
> - **CLI officielle recommandée** : `mobilesfrdth --help`
> - **CLI avancée / spécialisée** : `python -m sfrd.cli.run_campaign` seulement si vous travaillez déjà sur un pipeline SFRD identifié
> - **Flux historiques / reproduction** : `final/README.md` et `pretest_campagne/archive_or_mock/mobile-sfrd/README.md`
>
> Les autres interfaces présentes dans le dépôt sont conservées pour des usages avancés, historiques ou d’archive. **Ne les considérez pas comme des “CLI principales” concurrentes de `mobilesfrdth`.**


## Premier succès en 5 minutes

Depuis la **racine du dépôt** dans **PowerShell** :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

### 1. Lancer le dashboard

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

Le dashboard est la voie la plus simple pour vérifier rapidement que l'environnement est prêt et explorer un premier scénario interactif.

### 2. Lancer une campagne CLI minimale recommandée

```powershell
mobilesfrdth run --preset paper_fast --out runs/quickstart
```

Cette commande utilise **le point d’entrée officiel recommandé** pour produire une première campagne reproductible.

### 3. Agréger les résultats

```powershell
mobilesfrdth aggregate --results runs/quickstart --out runs/quickstart
```

### 4. Générer une première figure

```powershell
mobilesfrdth plots --aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory
```

### 5. Retrouver les sorties générées

- **Résultats bruts** : `runs/quickstart/results/`
- **Agrégats** : `runs/quickstart/aggregates/`
- **Figures** : `runs/quickstart/plots/`

> [!TIP]
> Si vous voulez simplement valider une première exécution sous Windows 11, ce parcours suffit : créer l'environnement, ouvrir le dashboard, lancer `mobilesfrdth run`, puis agréger et tracer les résultats.

## FAQ de démarrage

### Comment installer sous Windows 11 ?

Depuis la racine du dépôt dans **PowerShell**, créez un environnement virtuel puis installez le projet en mode editable :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

Cette procédure correspond au parcours standard documenté pour Windows 11.

### Comment lancer le dashboard ?

Activez l’environnement, puis exécutez :

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

Le dashboard est l’entrée recommandée pour un premier usage interactif.

### Comment lancer une simulation en CLI ?

Pour une première campagne reproductible en ligne de commande, utilisez la CLI officielle recommandée :

```powershell
mobilesfrdth run --preset paper_fast --out runs/quickstart
```

Complétez ensuite avec :

```powershell
mobilesfrdth aggregate --results runs/quickstart --out runs/quickstart
mobilesfrdth plots --aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory
```

### Où récupérer les CSV et les figures ?

- Les **résultats bruts** d’un premier essai `mobilesfrdth` sont placés dans `runs/quickstart/results/`.
- Les **CSV agrégés** sont écrits dans `runs/quickstart/aggregates/`.
- Les **figures** générées sont écrites dans `runs/quickstart/plots/`.
- Les flux historiques `final/data/` et `final/figures/` restent disponibles seulement pour la reproduction ou la comparaison avec d’anciens exports.

## Arborescence documentaire recommandée

- `README.md` : point d’entrée communauté.
- `docs/installation.md` : compatibilité plateforme, installation Python 3.11/3.12, scripts Bash/PowerShell et limitations connues.
- `docs/user_guide_dashboard.md` : premier usage du dashboard.
- `docs/user_guide_cli.md` : premier usage de la CLI `mobilesfrdth`.
- `docs/advanced_workflows.md` : workflows complets, génération de figures et pipelines spécialisés.
- `docs/archive_or_research/` : documentation historique, campagnes de reproduction, comparatifs et archives.
- `docker/README.md` : usage du runner CI local Docker et limites de ce support.

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

## Structure du dépôt : à quoi sert chaque dossier ?

La référence détaillée reste `docs/repository_map.md`, mais le tableau ci-dessous sert de **guide de lecture rapide** pour savoir **où aller en premier** selon votre besoin. Il couvre les dossiers visibles les plus utiles ou les plus ambigus du dépôt.

> [!TIP]
> **Parcours recommandé pour un premier usage** : commencez par `README.md`, puis `docs/user_guide_dashboard.md` ou `docs/user_guide_cli.md`. Les dossiers marqués **historiques** ou **secondaires** restent utiles pour la reproduction, la recherche ou la maintenance, mais ne sont pas le point d’entrée principal.

| Dossier | À quoi sert-il ? | Public cible | Statut | Ouvrir d’abord |
| --- | --- | --- | --- | --- |
| `src/` | Racine officielle du package Python installé par `pip install -e .`, notamment `src/mobilesfrdth/`. | Développeurs Python, mainteneurs CLI | **Officiel** | `README.md`, puis `docs/user_guide_cli.md` |
| `loraflexsim/` | Cœur applicatif du simulateur et du dashboard interactif. | Utilisateurs avancés, développeurs produit | **Officiel** | `docs/user_guide_dashboard.md` |
| `docs/` | Documentation utilisateur, technique, validation et workflows avancés. | Tous les publics | **Officiel** | `docs/user_guide_dashboard.md` ou `docs/user_guide_cli.md` selon l’entrée choisie |
| `tests/` | Tests automatisés unitaires, d’intégration et de non-régression du dépôt. | Développeurs, contributeurs, CI | **Officiel** | `docs/test_plan.md` |
| `scripts/` | Scripts utilitaires de bootstrap, validation, compatibilité Windows et automatisation. | Développeurs, mainteneurs, contributeurs | **Officiel / support** | `README.md`, puis les scripts concernés sous `scripts/windows/` si besoin |
| `config/` | Fichiers de configuration partagés pour les flux standards du simulateur. | Développeurs, mainteneurs | **Officiel / support** | `README.md` |
| `examples/` | Exemples de lancement et scripts simples d’analyse ou de démonstration. | Nouveaux utilisateurs, formateurs | **Officiel / secondaire** | `README.md` |
| `pretest_campagne/` | Racine des campagnes de recherche, reproductions métier et archives associées. | Équipe recherche, reproduction, analyse métier | **Secondaire / recherche** | `docs/archive_or_research/README.md` |
| `sfrd/` | CLI SFRD historique pour campagnes spécialisées distinctes du flux standard `mobilesfrdth`. | Utilisateurs experts SFRD, maintenance | **Historique / spécialisé** | `sfrd/README.md` |
| `final/` | Pipeline historique d’export CSV et de génération de figures pour reproduction ou comparaison rapide. | Utilisateurs avancés, reproduction, documentation | **Historique / secondaire** | `final/README.md` |
| `qos_cli/` | CLI spécialisée pour campagnes QoS, métriques, figures et rapports dédiés. | Utilisateurs QoS avancés, recherche | **Secondaire / spécialisé** | `qos_cli/README.md` |
| `experiments/` | Configurations d’expériences exploratoires conservées pour campagnes de recherche. | Recherche, benchmark, reproduction | **Secondaire / recherche** | Le `README.md` du sous-dossier concerné, par ex. `experiments/ucb1/README.md` |
| `mobile-sfrd_th/` | Archive legacy autour d’anciens presets, résultats et exemples ; ce n’est plus la source canonique du package. | Mainteneurs, archivage, comparaison historique | **Historique** | `mobile-sfrd_th/README.md` |
| `pretest_campagne/archive_or_mock/mobile-sfrd/` | Ancien mock pédagogique déplacé hors top-level pour éviter de le confondre avec le flux officiel. | Archivage, démonstration historique | **Historique / archive** | `pretest_campagne/archive_or_mock/mobile-sfrd/README.md` |
| `docker/` | Runner CI local et environnement conteneurisé minimal pour vérifier installation et tests. | Contributeurs, CI locale, intégration | **Officiel / support** | `docker/README.md` |
| `results/` | Résultats versionnés et sorties consolidées gardées comme références de reproduction. | Recherche, validation, comparaison | **Historique / archive** | `results/README.md` |
| `figures/` | Figures versionnées servant surtout d’archives ou de références documentaires. | Documentation, comparaison, reproduction | **Historique / archive** | `README.md`, puis les dossiers de figures utiles |
| `plots/` | Scripts ou artefacts de tracé transverses hors pipeline principal. | Développeurs, analyse technique | **Secondaire / support** | `docs/advanced_workflows.md` |
| `traffic/` | Composants et utilitaires liés au trafic réseau simulé. | Développeurs simulation, recherche | **Officiel / technique** | `docs/usage_scenarios.md` |
| `flora-master/` | Copie de référence externe liée à FLoRa, conservée pour comparaison scientifique et archive. | Recherche, comparaison académique | **Historique / archive** | `flora-master/README.md` |
| `numpy_stub/` et `scipy/` | Couches locales de compatibilité autour de dépendances scientifiques. | Mainteneurs, CI, environnements contraints | **Support technique** | `README.md` |
| `.github/` | Workflows GitHub Actions et automatisation du dépôt. | Mainteneurs, contributeurs CI | **Officiel / support** | Les fichiers sous `.github/workflows/` |

## Repères rapides selon votre besoin

- **Vous voulez utiliser le projet pour la première fois** : ouvrez `README.md`, puis `docs/user_guide_dashboard.md` ou `docs/user_guide_cli.md`.
- **Vous voulez lancer une campagne CLI standard** : utilisez `mobilesfrdth`.
- **Vous cherchez un pipeline SFRD spécialisé** : allez vers `sfrd/` en sachant qu’il s’agit d’une CLI avancée, pas de l’entrée officielle recommandée.
- **Vous cherchez des campagnes de reproduction ou des archives métier** : commencez par `pretest_campagne/`, `final/`, `pretest_campagne/archive_or_mock/mobile-sfrd/` ou `docs/archive_or_research/` selon le pipeline visé.
- **Vous hésitez entre plusieurs interfaces** : privilégiez toujours `mobilesfrdth` et le dashboard `loraflexsim/`; les autres interfaces sont là pour des besoins avancés, historiques ou archivés.

## Notes de gouvernance utiles

- **`src/mobilesfrdth/`** est **l’implémentation officielle** de la CLI `mobilesfrdth` à conserver et à faire évoluer.
- **`sfrd/`** reste une CLI **avancée / spécialisée**.
- **`final/`** et **`pretest_campagne/archive_or_mock/mobile-sfrd/`** relèvent des **flux historiques / reproduction**.
- **`mobile-sfrd_th/`** est **une archive legacy** : utile pour relire des artefacts historiques, mais pas comme source canonique du package.
- **Tout dossier déplacé dans un espace d’archives** doit être compris comme **non prioritaire pour un nouvel utilisateur**.

## Vérification avant contribution

Depuis la racine du dépôt :

```bash
make validate
```

Sous Windows, utilisez un terminal disposant de `make` (Git Bash, WSL ou équivalent).
