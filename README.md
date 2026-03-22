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

La référence détaillée est maintenue dans `docs/repository_map.md`. Le tableau ci-dessous donne la **vue visible depuis le README** afin qu'aucun dossier top-level structurant ne reste sans statut explicite.

| Dossier | Catégorie | Statut visible | Action décidée |
| --- | --- | --- | --- |
| `.github/` | conteneur / CI | Workflows GitHub et automatisation du dépôt. | conserver tel quel comme point d’entrée officiel |
| `config/` | produit principal / flux standard | Configuration partagée du simulateur. | conserver tel quel comme point d’entrée officiel |
| `docker/` | conteneur / CI | Référence officielle pour la conteneurisation. | conserver tel quel comme point d’entrée officiel |
| `docs/` | produit principal / flux standard | Documentation active et gouvernance du dépôt. | conserver tel quel comme point d’entrée officiel |
| `examples/` | outillage / packaging | Scripts d'exemple pour prise en main. | conserver tel quel comme point d’entrée officiel |
| `experiments/` | recherche / archive | Configurations exploratoires à rapprocher des campagnes de recherche. | déplacer sous `pretest_campagne/` |
| `figures/` | recherche / archive | Figures versionnées servant surtout de référence. | convertir en simple archive/documentation |
| `final/` | compatibilité / legacy | Pipeline historique de reproduction CSV/figures. | convertir en simple archive/documentation |
| `flora-master/` | recherche / archive | Copie de référence externe liée à FLoRa. | convertir en simple archive/documentation |
| `loraflexsim/` | produit principal / flux standard | Cœur applicatif du dashboard et du simulateur. | conserver tel quel comme point d’entrée officiel |
| `mobile-sfrd/` | recherche / archive | Générateur expérimental séparé du flux principal. | convertir en simple archive/documentation |
| `mobile-sfrd_th/` | compatibilité / legacy | Ancien squelette redondant avec le package officiel. | fusionner avec un autre dossier (`src/mobilesfrdth/`) |
| `numpy_stub/` | compatibilité / legacy | Stub de compatibilité local. | conserver tel quel comme point d’entrée officiel |
| `plots/` | outillage / packaging | Scripts de tracé transverses. | conserver tel quel comme point d’entrée officiel |
| `pretest_campagne/` | recherche / archive | Racine officielle des campagnes de recherche et de reproduction. | conserver tel quel comme point d’entrée officiel |
| `qos_cli/` | compatibilité / legacy | CLI spécialisée hors parcours standard. | convertir en simple archive/documentation |
| `results/` | recherche / archive | Résultats consolidés conservés comme référence. | convertir en simple archive/documentation |
| `scipy/` | compatibilité / legacy | Support de compatibilité local autour de SciPy. | conserver tel quel comme point d’entrée officiel |
| `scripts/` | outillage / packaging | Automatisation, bootstrap et validation. | conserver tel quel comme point d’entrée officiel |
| `sfrd/` | compatibilité / legacy | CLI SFRD avancée, distincte de `mobilesfrdth`. | convertir en simple archive/documentation |
| `src/` | produit principal / flux standard | Racine officielle du code Python packagé. | conserver tel quel comme point d’entrée officiel |
| `tests/` | produit principal / flux standard | Base de validation automatique du dépôt. | conserver tel quel comme point d’entrée officiel |
| `traffic/` | produit principal / flux standard | Composants trafic et utilitaires réseau. | conserver tel quel comme point d’entrée officiel |

### Décision explicite sur le dossier `src/mobilesfrdth/`

Bien qu'il ne soit pas top-level, `src/mobilesfrdth/` fait partie des cas à clarifier : c'est **l'implémentation officielle** de la CLI `mobilesfrdth`, à **conserver tel quel comme point d’entrée officiel**, tandis que `mobile-sfrd_th/` est à **fusionner** vers cette implémentation de référence.

## Vérification avant contribution

Depuis la racine du dépôt :

```bash
make validate
```

Sous Windows, utilisez un terminal disposant de `make` (Git Bash, WSL ou équivalent).
