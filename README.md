# LoRaFlexSim 1.0.1 : accueil communauté

LoRaFlexSim est un simulateur LoRa/LoRaWAN en Python pour explorer des scénarios radio, de mobilité et d'ADR, via un dashboard interactif ou une CLI reproductible.

Ce dépôt est destiné à la communauté : le simulateur peut être utilisé librement, la documentation privilégie une prise en main rapide, et le parcours de lecture distingue clairement l’usage standard recommandé des workflows avancés, de recherche ou de reproduction.

## Commencer ici

Si vous découvrez le dépôt, retenez seulement ceci :

- **Point d’entrée recommandé pour une campagne reproductible** : `mobilesfrdth`
- **Point d’entrée recommandé pour un test visuel rapide** : `panel serve loraflexsim/launcher/dashboard.py --show`
- **Documentation de premier niveau** : `docs/user_guide_dashboard.md` et `docs/user_guide_cli.md`

### Mini-parcours décisionnel

- **Je veux tester visuellement** → utilisez le **dashboard** : `panel serve loraflexsim/launcher/dashboard.py --show`
- **Je veux lancer une campagne reproductible** → utilisez **`mobilesfrdth`**
- **Je veux reproduire un ancien pipeline** → allez vers **`final/`** ou **`pretest_campagne/...`**
- **Je veux une CLI spécialisée** → regardez **`sfrd/`** ou **`qos_cli/`**

> [!TIP]
> Si vous hésitez entre plusieurs entrées, commencez par **le dashboard** pour explorer, ou par **`mobilesfrdth`** pour une campagne standard. Les autres chemins sont surtout utiles pour des besoins spécialisés, historiques ou de reproduction.

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

Repères utiles :

- **Version recommandée** : Python 3.11
- **Plage prise en charge par le packaging** : Python 3.11 à 3.12
- **Wrappers de bootstrap** : `./scripts/bootstrap_windows.ps1` et `./scripts/bootstrap_unix.sh`
- **Installation standard recommandée** : `python -m pip install -e . --no-build-isolation`

> [!NOTE]
> La matrice complète de compatibilité plateforme, les scripts par shell et les modes fallback détaillés sont regroupés plus bas dans ce document et dans `docs/installation.md`.

## Première exécution

Depuis la racine du dépôt, après activation de l’environnement :

### 1. Vérifier rapidement l’installation avec le dashboard

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

Le dashboard est le chemin le plus simple pour valider visuellement que l’environnement fonctionne.

### 2. Lancer une première campagne CLI reproductible

```powershell
mobilesfrdth run --preset paper_fast --out runs/quickstart
```

### 3. Agréger puis générer une première figure

```powershell
mobilesfrdth aggregate --results runs/quickstart --out runs/quickstart
mobilesfrdth plots --aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory
```

### 4. Retrouver les sorties générées

- **Résultats bruts** : `runs/quickstart/results/`
- **Agrégats** : `runs/quickstart/aggregates/`
- **Figures** : `runs/quickstart/plots/`

## Comprendre la structure du dépôt

Pour réduire la charge cognitive, vous pouvez lire le dépôt avec seulement ces repères :

- **`loraflexsim/`** : cœur du simulateur et dashboard interactif.
- **`src/`** : package Python officiel, notamment `src/mobilesfrdth/`.
- **`docs/`** : documentation utilisateur, technique et workflows avancés.
- **`final/`** et **`pretest_campagne/`** : reproduction, recherche et pipelines historiques ; dans `final/`, les points d’entrée actuels sont `final/scenarios/`, `final/plots/` et `final/run_all.*`.
- **`sfrd/`** et **`qos_cli/`** : CLIs spécialisées pour besoins experts.

### Tableau de lecture rapide

| Besoin | Où aller d’abord ? | Pourquoi |
| --- | --- | --- |
| Tester visuellement | `loraflexsim/` puis `docs/user_guide_dashboard.md` | Le dashboard est la porte d’entrée la plus directe. |
| Lancer une campagne standard | `src/mobilesfrdth/` puis `docs/user_guide_cli.md` | `mobilesfrdth` est l’entrée officielle recommandée. |
| Reproduire un flux historique | `final/README.md` ou `pretest_campagne/` | `final/README.md` renvoie vers les entrées encore actives (`final/scenarios/`, `final/plots/`, `final/run_all.*`) ; `pretest_campagne/` couvre les autres campagnes de reproduction. |
| Utiliser une interface experte | `sfrd/` ou `qos_cli/` | Ces CLIs couvrent des besoins spécialisés, pas le parcours standard. |

> [!TIP]
> Le tableau détaillé dossier par dossier est conservé plus bas dans **« Structure du dépôt : à quoi sert chaque dossier ? »** pour éviter de surcharger la première page.

## Références détaillées de démarrage

Les sections de démarrage redondantes ont été fusionnées dans les quatre blocs ci-dessus. Pour le détail selon votre usage, utilisez directement les guides de référence :

- **Installation complète, compatibilité plateforme et fallbacks** : `docs/installation.md`
- **Premier usage du dashboard** : `docs/user_guide_dashboard.md`
- **Premier workflow CLI reproductible avec `mobilesfrdth`** : `docs/user_guide_cli.md`
- **Workflows avancés, export et reproduction** : `docs/advanced_workflows.md`, `docs/archive_or_research/` et `final/README.md` pour le pipeline historique `final/`

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
- **Linux et macOS sont documentés explicitement** via `docs/installation.md`, l’inventaire `docs/user_entrypoints_inventory.md` et les wrappers Bash `scripts/bootstrap_unix.sh`, `scripts/mobilesfrdth.sh`, `scripts/run_campaign_profiles.sh`, `scripts/run_grid.sh` et `scripts/run_offline.sh`.
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
./scripts/run_offline.sh
```

Dans ce mode seulement, certains scripts positionnent **`PYTHONPATH=src`** automatiquement. **Vous n’avez pas besoin de définir `PYTHONPATH=src` pour l’installation standard.**

➡ Voir `docs/installation.md` pour la matrice complète, les scripts par shell et les limitations connues.

## Références ciblées après le premier démarrage

Les anciennes sections **« Démarrage rapide Windows 11 »**, **« Premier succès en 5 minutes »** et **« FAQ de démarrage »** ont été volontairement fusionnées avec **« Installation recommandée »** et **« Première exécution »** pour éviter les doublons.

Utilisez désormais ces références canoniques selon votre besoin :

- **Réinstaller ou adapter les commandes à votre shell** : `docs/installation.md`
- **Retrouver le lancement guidé du dashboard** : `docs/user_guide_dashboard.md`
- **Retrouver le workflow CLI complet (`run`, `aggregate`, `plots`, `validate`)** : `docs/user_guide_cli.md`
- **Consulter les flux historiques ou spécialisés** : `docs/archive_or_research/`, `final/README.md`, `sfrd/README.md` et `qos_cli/README.md` ; évitez d’inférer d’anciens sous-chemins documentaires comme `final/data/` ou `final/figures/`, remplacés par la documentation locale et les sous-dossiers actuels de `final/`.

## Arborescence documentaire recommandée

- `README.md` : point d’entrée communauté.
- `docs/installation.md` : compatibilité plateforme, installation Python 3.11/3.12, scripts Bash/PowerShell et limitations connues.
- `docs/user_guide_dashboard.md` : premier usage du dashboard.
- `docs/user_guide_cli.md` : premier usage de la CLI `mobilesfrdth`.
- `docs/advanced_workflows.md` : workflows complets, génération de figures et positionnement des pipelines spécialisés ; pour le détail opérationnel du pipeline historique `final/`, basculez vers `final/README.md`.
- `docs/archive_or_research/` : documentation historique, campagnes de reproduction, comparatifs et archives.
- `docker/README.md` : usage du runner CI local Docker et limites de ce support.

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
| `src/` | Racine officielle du package Python installé par `pip install -e .`, notamment `src/mobilesfrdth/`. | Développeurs Python, mainteneurs CLI | **Officiel** | `src/README.md`, puis `docs/user_guide_cli.md` |
| `loraflexsim/` | Cœur applicatif du simulateur et du dashboard interactif. | Utilisateurs avancés, développeurs produit | **Officiel** | `loraflexsim/README.md`, puis `docs/user_guide_dashboard.md` |
| `docs/` | Documentation utilisateur, technique, validation et workflows avancés. | Tous les publics | **Officiel** | `docs/README.md`, puis `docs/user_guide_dashboard.md` ou `docs/user_guide_cli.md` |
| `tests/` | Tests automatisés unitaires, d’intégration et de non-régression du dépôt. | Développeurs, contributeurs, CI | **Officiel** | `tests/README.md`, puis `docs/test_plan.md` |
| `scripts/` | Scripts utilitaires de bootstrap, validation, compatibilité Windows et automatisation. | Développeurs, mainteneurs, contributeurs | **Officiel / support** | `scripts/README.md`, puis les scripts concernés sous `scripts/windows/` si besoin |
| `config/` | Fichiers de configuration partagés pour les flux standards du simulateur. | Développeurs, mainteneurs | **Officiel / support** | `config/README.md` |
| `examples/` | Exemples de lancement et scripts simples d’analyse ou de démonstration. | Nouveaux utilisateurs, formateurs | **Officiel / secondaire** | `examples/README.md` |
| `pretest_campagne/` | Racine des campagnes de recherche, reproductions métier et archives associées. | Équipe recherche, reproduction, analyse métier | **Secondaire / recherche** | `pretest_campagne/README.md`, puis `docs/archive_or_research/README.md` |
| `sfrd/` | CLI SFRD historique pour campagnes spécialisées distinctes du flux standard `mobilesfrdth`. | Utilisateurs experts SFRD, maintenance | **Historique / spécialisé** | `sfrd/README.md` |
| `final/` | Pipeline historique de reproduction avec scripts de lancement (`run_all.*`), scénarios (`final/scenarios/`) et scripts de tracé (`final/plots/`) ; les anciennes références du type `final/data/` ou `final/figures/` ne correspondent plus à l’arborescence actuelle. | Utilisateurs avancés, reproduction, documentation | **Historique / secondaire** | `final/README.md` |
| `qos_cli/` | CLI spécialisée pour campagnes QoS, métriques, figures et rapports dédiés. | Utilisateurs QoS avancés, recherche | **Secondaire / spécialisé** | `qos_cli/README.md` |
| `experiments/` | Configurations d’expériences exploratoires conservées pour campagnes de recherche. | Recherche, benchmark, reproduction | **Secondaire / recherche** | `experiments/README.md`, puis le `README.md` du sous-dossier concerné |
| `mobile-sfrd_th/` | Archive legacy autour d’anciens presets, résultats et exemples ; ce n’est plus la source canonique du package. | Mainteneurs, archivage, comparaison historique | **Historique** | `mobile-sfrd_th/README.md` |
| `pretest_campagne/archive_or_mock/mobile-sfrd/` | Ancien mock pédagogique déplacé hors top-level pour éviter de le confondre avec le flux officiel. | Archivage, démonstration historique | **Historique / archive** | `pretest_campagne/archive_or_mock/mobile-sfrd/README.md` |
| `docker/` | Runner CI local et environnement conteneurisé minimal pour vérifier installation et tests. | Contributeurs, CI locale, intégration | **Officiel / support** | `docker/README.md` |
| `results/` | Résultats versionnés et sorties consolidées gardées comme références de reproduction. | Recherche, validation, comparaison | **Historique / archive** | `results/README.md` |
| `figures/` | Figures versionnées conservées comme archives documentaires globales du dépôt ; ce dossier ne remplace pas `final/plots/` pour le pipeline historique `final/`. | Documentation, comparaison, reproduction | **Historique / archive** | `figures/README.md` |
| `plots/` | Scripts ou artefacts de tracé transverses hors pipeline principal. | Développeurs, analyse technique | **Secondaire / support** | `plots/README.md`, puis `docs/advanced_workflows.md` |
| `traffic/` | Composants et utilitaires liés au trafic réseau simulé. | Développeurs simulation, recherche | **Officiel / technique** | `traffic/README.md`, puis `docs/usage_scenarios.md` |
| `flora-master/` | Copie de référence externe liée à FLoRa, conservée pour comparaison scientifique et archive. | Recherche, comparaison académique | **Historique / archive** | `flora-master/README.md` |
| `numpy_stub/` et `scipy/` | Couches locales de compatibilité autour de dépendances scientifiques. | Mainteneurs, CI, environnements contraints | **Support technique** | `numpy_stub/README.md` et `scipy/README.md` |
| `.github/` | Workflows GitHub Actions et automatisation du dépôt. | Mainteneurs, contributeurs CI | **Officiel / support** | Les fichiers sous `.github/workflows/` |

## Repères rapides selon votre besoin

- **Vous voulez utiliser le projet pour la première fois** : ouvrez `README.md`, puis `docs/user_guide_dashboard.md` ou `docs/user_guide_cli.md`.
- **Vous voulez lancer une campagne CLI standard** : utilisez `mobilesfrdth`.
- **Vous cherchez un pipeline SFRD spécialisé** : allez vers `sfrd/` en sachant qu’il s’agit d’une CLI avancée, pas de l’entrée officielle recommandée.
- **Vous cherchez des campagnes de reproduction ou des archives métier** : commencez par `final/README.md` pour le pipeline historique `final/`, puis `pretest_campagne/`, `pretest_campagne/archive_or_mock/mobile-sfrd/` ou `docs/archive_or_research/` selon le pipeline visé.
- **Vous hésitez entre plusieurs interfaces** : privilégiez toujours `mobilesfrdth` et le dashboard `loraflexsim/`; les autres interfaces sont là pour des besoins avancés, historiques ou archivés.

## Notes de gouvernance utiles

- **`src/mobilesfrdth/`** est **l’implémentation officielle** de la CLI `mobilesfrdth` à conserver et à faire évoluer.
- **`sfrd/`** reste une CLI **avancée / spécialisée**.
- **`final/`** et **`pretest_campagne/archive_or_mock/mobile-sfrd/`** relèvent des **flux historiques / reproduction** ; pour `final/`, la documentation à jour pointe vers `final/run_all.*`, `final/scenarios/` et `final/plots/`, pas vers d’anciens chemins comme `final/data/` ou `final/figures/`.
- **`mobile-sfrd_th/`** est **une archive legacy** : utile pour relire des artefacts historiques, mais pas comme source canonique du package.
- **Tout dossier déplacé dans un espace d’archives** doit être compris comme **non prioritaire pour un nouvel utilisateur**.

## Vérification avant contribution

Depuis la racine du dépôt :

```bash
make validate
```

Sous Windows, utilisez un terminal disposant de `make` (Git Bash, WSL ou équivalent).
