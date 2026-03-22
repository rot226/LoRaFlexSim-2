# Guide utilisateur — CLI communauté

La CLI officielle mise en avant pour la communauté est **`mobilesfrdth`**. Elle couvre le flux stable recommandé pour lancer une campagne, agréger les résultats, générer des figures puis valider les sorties.

## Positionnement des points d’entrée

Pour éviter toute ambiguïté entre plusieurs CLI présentes dans le dépôt :

- **Point d’entrée officiel recommandé** : `mobilesfrdth`
- **Points d’entrée avancés / spécialisés** : `sfrd`
- **Flux historiques / reproduction** : `final`, `mobile-sfrd`
- **Archives / anciens pipelines** : tout dossier déplacé sous l’espace d’archives

Si vous ne savez pas encore quelle commande utiliser, **choisissez `mobilesfrdth`**.

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

## Que faire si vous hésitez avec une autre CLI ?

- **Vous voyez `sfrd`** : gardez-le pour un pipeline avancé / spécialisé déjà identifié.
- **Vous voyez `final`** : gardez-le pour un flux historique de reproduction ou de comparaison.
- **Vous voyez `mobile-sfrd`** : considérez-le comme un flux historique conservé pour archive et reproduction légère.
- **Vous tombez sur un dossier d’archives** : ne l’utilisez pas comme point de départ pour une nouvelle campagne.

## Interfaces secondaires

Les interfaces ci-dessous existent toujours mais ne sont pas nécessaires pour un premier usage :

- `qos_cli/README.md` pour la CLI QoS spécialisée ;
- `sfrd/README.md` pour le pipeline SFRD avancé ;
- `final/README.md` pour des scripts historiques d’export/reproduction ;
- `pretest_campagne/archive_or_mock/mobile-sfrd/README.md` pour le mock historique `mobile-sfrd` ;
- `docs/archive_or_research/` pour les contenus archivés, de reproduction et de recherche ;
- `pretest_campagne/scenario_c/README.md` pour le pipeline de reproduction du scénario C.
