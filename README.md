# LoRaFlexSim 1.0.1 : accueil communauté

LoRaFlexSim est un simulateur LoRa/LoRaWAN en Python pour explorer des scénarios radio, de mobilité et d'ADR, via un dashboard interactif ou une CLI reproductible.

Ce dépôt est destiné à la communauté : le simulateur peut être utilisé librement, la documentation privilégie une prise en main rapide, et le parcours de lecture distingue clairement l’usage standard recommandé des workflows avancés, de recherche ou de reproduction.

## Politique d’installation et d’exécution

### Plateforme documentée en priorité

- **OS officiellement documenté en priorité : Windows 11**.
- Les commandes ci-dessous sont **rédigées et maintenues pour Windows 11 avec PowerShell**, en partant de la **racine du dépôt**.
- **`cmd.exe` n’est pas la cible documentaire principale** : certaines commandes peuvent fonctionner, mais elles ne sont pas harmonisées ici.

### Version Python

- **Version recommandée : Python 3.11**.
- **Versions prises en charge par le packaging : Python 3.11 à 3.12**.
- Si plusieurs versions sont installées sous Windows, utilisez de préférence **`py -3.11`** pour éviter les ambiguïtés.

### Méthode d’installation recommandée

Depuis la **racine du dépôt** dans **PowerShell** :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

Cette méthode est la référence pour toute la documentation de ce dépôt.

L'installation editable canonique expose désormais **une seule distribution Python et une seule arborescence source pour `mobilesfrdth`** : `pyproject.toml` pointe sur `src/mobilesfrdth/`, et l'ancien doublon `mobile-sfrd_th/src/mobilesfrdth/` ne doit plus être utilisé.

### Méthode offline / fallback

> [!IMPORTANT]
> **Mode fallback à utiliser seulement si l’installation editable échoue**.

Le mode fallback ne remplace pas la méthode standard. Il sert uniquement aux environnements Windows 11 où `pip install -e . --no-build-isolation` ne peut pas être finalisé.

Depuis la **racine du dépôt** dans **PowerShell** :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File scripts/windows/run_offline.ps1
```

Dans ce mode seulement, certains scripts positionnent **`PYTHONPATH=src`** automatiquement. **Vous n’avez pas besoin de définir `PYTHONPATH=src` pour l’installation standard.**

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
> - **CLI communauté** : `mobilesfrdth --help`
>
> Les autres interfaces présentes dans le dépôt sont conservées pour des usages avancés, historiques ou de reproduction.


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

### 2. Lancer une simulation CLI minimale

```powershell
python -m loraflexsim.run --nodes 30 --gateways 1 --mode random --interval 10 --steps 100 --output final/data/simulation.csv
```

Cette commande produit un CSV minimal dans : `final/data/simulation.csv`.

### 3. Retrouver le CSV généré

- **CSV produit** : `final/data/simulation.csv`
- Ce fichier peut ensuite être ouvert dans Excel, importé dans un notebook ou réutilisé pour tracer une figure.

### 4. Trouver ou générer une figure

- **Emplacement habituel des figures** : `final/figures/`
- Pour générer une figure simple à partir du CSV précédent :

```powershell
python examples/analyse_resultats.py final/data/simulation.csv --output-dir final/figures --basename pdr_by_nodes
```

La figure sera alors écrite dans `final/figures/`.

> [!TIP]
> Si vous voulez simplement valider une première exécution sous Windows 11, ce parcours suffit : créer l'environnement, ouvrir le dashboard, lancer une simulation CLI, puis générer une figure à partir du CSV produit.

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

Pour une première simulation reproductible en ligne de commande :

```powershell
python -m loraflexsim.run --nodes 30 --gateways 1 --mode random --interval 10 --steps 100 --output final/data/simulation.csv
```

Cette commande écrit un fichier CSV exploitable immédiatement.

### Où récupérer les CSV et les figures ?

- Les **CSV** d’exemple ou générés lors d’un premier essai sont généralement placés dans `final/data/`.
- Les **figures** générées sont généralement écrites dans `final/figures/`.
- Le document `docs/advanced_workflows.md` détaille ensuite les exports, traitements et pipelines avancés.

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

## Carte du dépôt et statut des dossiers top-level

La référence détaillée est maintenue dans `docs/repository_map.md`. Le tableau ci-dessous donne la **vue visible depuis le README** avec, pour chaque dossier top-level, une description d’une phrase et son statut dans le parcours recommandé.

| Dossier | Description | Statut dans le parcours recommandé |
| --- | --- | --- |
| `.github/` | Contient les workflows GitHub et l’automatisation du dépôt. | Support officiel du dépôt. |
| `config/` | Regroupe la configuration partagée utilisée par le simulateur et ses outils. | Flux standard. |
| `docker/` | Fournit les éléments de conteneurisation et d’environnement reproductible. | Support officiel du dépôt. |
| `docs/` | Centralise la documentation active, les guides utilisateur et la gouvernance. | Flux standard. |
| `examples/` | Propose des scripts d’exemple pour la prise en main et l’analyse rapide. | Flux standard. |
| `experiments/` | Conserve des configurations exploratoires liées aux campagnes de recherche. | Historique / recherche. |
| `figures/` | Archive des figures versionnées servant surtout de référence documentaire. | Historique / archive. |
| `final/` | Conserve le pipeline historique d’export CSV/figures pour reproduction et comparaison rapide. | Historique / secondaire. |
| `flora-master/` | Garde une copie de référence externe liée à FLoRa pour comparaison ou archive. | Historique / archive. |
| `loraflexsim/` | Héberge le cœur applicatif du dashboard et du simulateur. | Flux standard. |
| `mobile-sfrd_th/` | Maintient une archive legacy documentée maintenant séparée du code packagé officiel. | Historique / archive. |
| `numpy_stub/` | Fournit un stub local de compatibilité autour de NumPy. | Support technique. |
| `plots/` | Regroupe des scripts de tracé transverses réutilisables. | Outillage standard. |
| `pretest_campagne/` | Rassemble les campagnes de recherche, de reproduction et l’espace `archive_or_mock/`. | Recherche / reproduction avancée. |
| `qos_cli/` | Préserve une CLI QoS spécialisée hors du premier parcours utilisateur. | Historique / secondaire. |
| `results/` | Stocke des résultats consolidés gardés comme référence ou preuve de reproduction. | Historique / archive. |
| `scipy/` | Ajoute une couche locale de compatibilité autour de SciPy. | Support technique. |
| `scripts/` | Réunit les scripts d’automatisation, de bootstrap et de validation. | Outillage standard. |
| `sfrd/` | Conserve une CLI historique avancée pour campagnes SFRD et calibrations spécifiques. | Historique / secondaire. |
| `src/` | Porte la racine officielle du code Python packagé. | Flux standard. |
| `tests/` | Contient la base de validation automatique et des tests du dépôt. | Flux standard. |
| `traffic/` | Héberge des composants trafic et des utilitaires réseau utilisés par le simulateur. | Flux standard. |

### Décision explicite sur le dossier `src/mobilesfrdth/`

Bien qu'il ne soit pas top-level, `src/mobilesfrdth/` fait partie des cas à clarifier : c'est **l'implémentation officielle** de la CLI `mobilesfrdth`, à **conserver tel quel comme point d’entrée officiel**. L'ancien doublon `mobile-sfrd_th/src/mobilesfrdth/` a été supprimé ; `mobile-sfrd_th/` ne sert plus que d'archive documentaire.

### Décision explicite sur le dossier déplacé `pretest_campagne/archive_or_mock/mobile-sfrd/`

L’ancien dossier top-level `mobile-sfrd/` a été déplacé sous `pretest_campagne/archive_or_mock/mobile-sfrd/`. Son statut retenu est : **archive d’un mock pédagogique historique**. Il n’est plus un point d’entrée recommandé ; pour le flux standard, utilisez `mobilesfrdth`.

## Vérification avant contribution

Depuis la racine du dépôt :

```bash
make validate
```

Sous Windows, utilisez un terminal disposant de `make` (Git Bash, WSL ou équivalent).
