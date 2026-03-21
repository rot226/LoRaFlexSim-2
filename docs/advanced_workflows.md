# Workflows avancés

Ce document regroupe les pipelines complets utiles après la prise en main initiale du projet.

## 1. Génération et export avancés de figures

Le guide détaillé de génération des figures du pipeline scénario C a été déplacé depuis `README_FIGURES.md`.

### Emplacements de résultats attendus

Depuis Windows 11, lancez les commandes depuis la racine du dépôt et vérifiez les sorties suivantes :

- `results/pretest_campagne/scenario_c/step1/`
- `results/pretest_campagne/scenario_c/step2/`

Ces sorties servent de base aux scripts de génération de figures et d’exports consolidés.

### Figures documentées

- **Figure 1** : comparaison PDR / DER vs nombre de nœuds ;
- **Figure 2** : indice de Jain vs nombre de nœuds ;
- **Figure 3** : throughput vs nombre de nœuds.

### Exports typiques

- `figures/pretest_campagne/scenario_c/step1/step1_pdr_der_comparison.png`
- `figures/pretest_campagne/scenario_c/step1/step1_pdr_der_comparison.pdf`
- `figures/pretest_campagne/scenario_c/step1/step1_jain_comparison.png`
- `figures/pretest_campagne/scenario_c/step1/step1_jain_comparison.pdf`
- `figures/pretest_campagne/scenario_c/step1/step1_throughput_comparison.png`
- `figures/pretest_campagne/scenario_c/step1/step1_throughput_comparison.pdf`

## 2. Pipeline avancé du scénario C

Le pipeline scénario C fournit un flux de reproduction plus riche que le parcours communauté.

### Organisation

- `pretest_campagne/scenario_c/common/` : utilitaires partagés ;
- `pretest_campagne/scenario_c/step1/` : première étape ;
- `pretest_campagne/scenario_c/step2/` : seconde étape ;
- `pretest_campagne/scenario_c/run_all.py` : orchestration globale ;
- `pretest_campagne/scenario_c/make_all_plots.py` : génération complète des graphes.

### Workflow Windows 11 recommandé

```powershell
python -m pretest_campagne.scenario_c.run_all --network-sizes 80 160 320 640 1280 --replications 5 --seeds_base 1
python -m pretest_campagne.scenario_c.make_all_plots --formats png,eps,pdf --no-suptitle
python -m pretest_campagne.scenario_c.all_plot_compare --export-csv --output-dir figures/pretest_campagne/scenario_c/compare_all
```

### Usage conseillé

Utilisez ce pipeline si vous devez :

- reproduire des résultats de recherche ;
- générer des comparatifs détaillés ;
- produire un manifeste de figures et des diagnostics scientifiques.

## 3. Pipeline SFRD spécialisé

Le dossier `sfrd/` correspond à une CLI spécialisée, distincte de l’interface communauté `mobilesfrdth`.

### Workflow standard

```powershell
python -m sfrd.cli.run_campaign --network-sizes 80 160 320 640 1280 --replications 5 --seeds-base 1 --snir OFF,ON --algos UCB ADR MixRA-H MixRA-Opt --warmup-s 0
python -m sfrd.cli.validate_outputs --output-root sfrd/logs/<campaign_id>/output
python -m sfrd.cli.plot_campaign --campaign-id <campaign_id>
```

### Cas d’usage

Ce flux est utile si vous travaillez spécifiquement sur :

- les campagnes SFRD ;
- l’agrégation avancée ;
- l’analyse des récompenses UCB ;
- la calibration de paramètres UCB.

## 4. Où trouver l’historique et les campagnes de recherche ?

Les contenus hérités, de reproduction et d’archive sont maintenant regroupés sous `docs/archive_or_research/`.
