# Guide utilisateur — CLI communauté

La CLI officielle mise en avant pour la communauté est **`mobilesfrdth`**. Elle couvre le flux stable recommandé pour lancer une campagne, agréger les résultats, générer des figures puis valider les sorties.

## Vérifier l’installation

```powershell
mobilesfrdth --help
```

Si l’entrypoint n’est pas encore disponible, utilisez :

```powershell
python -m mobilesfrdth --help
```

## Workflow minimal recommandé

### 1. Lister les presets disponibles

```powershell
mobilesfrdth presets --list
```

### 2. Lancer une simulation

Option preset canonique :

```powershell
mobilesfrdth run --preset paper_fast --out runs/quickstart
```

Option explicite avec config + profil :

```powershell
mobilesfrdth run --config experiments/default.yaml --out runs/quickstart --profile smoke
```

### 3. Agréger les résultats

```powershell
mobilesfrdth aggregate --results runs/quickstart --out runs/quickstart
```

### 4. Générer les figures

```powershell
mobilesfrdth plots --aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory
```

### 5. Valider les agrégats

```powershell
mobilesfrdth validate --aggregates-dir runs/quickstart/aggregates
```

## Rôle de chaque étape

- **presets** : affiche les presets canonisés de campagne ;
- **run** : exécute la campagne et écrit les sorties dans `runs/quickstart/` ;
- **aggregate** : consolide les résultats bruts dans `runs/quickstart/aggregates/` ;
- **plots** : génère les figures dans `runs/quickstart/plots/` ;
- **validate** : contrôle la cohérence des agrégats.

## Quand utiliser la CLI ?

Utilisez cette CLI si vous voulez :

- rejouer exactement une campagne ;
- enchaîner plusieurs traitements de façon reproductible ;
- automatiser un protocole expérimental ;
- intégrer le flux à un script Windows, à CI ou à un pipeline d’analyse.

Le package Python canonique est `mobilesfrdth` et son unique arborescence source est `src/mobilesfrdth/`. L'ancien doublon `mobile-sfrd_th/src/mobilesfrdth/` ne fait plus partie du flux d'installation editable.

## Interfaces secondaires

Les interfaces ci-dessous existent toujours mais ne sont pas nécessaires pour un premier usage :

- `qos_cli/README.md` pour la CLI QoS spécialisée ;
- `sfrd/README.md` pour le pipeline SFRD avancé ;
- `final/README.md` pour des scripts historiques d’export/reproduction ;
- `pretest_campagne/iwcmc_archive/README.md` pour l’archive métier `iwcmc_archive` ;
- `pretest_campagne/scenario_c/README.md` pour le pipeline de reproduction du scénario C.
