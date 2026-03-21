# Workflows avancés

Ce document regroupe les pipelines complets utiles après la prise en main initiale du projet.

## 1. Génération et export avancés de figures

Le guide détaillé de génération des figures issues du scénario C a été déplacé depuis `README_FIGURES.md`.

### Emplacements de résultats attendus

- `article_c/step1/results`
- `article_c/step2/results`

Ces sorties servent de base aux scripts de génération de figures et d’exports consolidés.

### Figures documentées

- **Figure 1** : comparaison PDR / DER vs nombre de nœuds ;
- **Figure 2** : indice de Jain vs nombre de nœuds ;
- **Figure 3** : throughput vs nombre de nœuds.

### Exports typiques

- `figures/step1/step1_pdr_der_comparison.png`
- `figures/step1/step1_pdr_der_comparison.pdf`
- `figures/step1/step1_jain_comparison.png`
- `figures/step1/step1_jain_comparison.pdf`
- `figures/step1/step1_throughput_comparison.png`
- `figures/step1/step1_throughput_comparison.pdf`

## 2. Pipeline avancé du scénario C

Le scénario C fournit un pipeline de reproduction plus riche que le flux communauté.

### Organisation

- `article_c/common/` : utilitaires partagés ;
- `article_c/step1/` : première étape ;
- `article_c/step2/` : seconde étape ;
- `article_c/run_all.py` : orchestration globale ;
- `article_c/make_all_plots.py` : génération complète des graphes.

### Workflow Windows 11 recommandé

```powershell
python -m article_c.run_all --network-sizes 80 160 320 640 1280 --replications 5 --seeds_base 1
python -m article_c.make_all_plots --formats png,eps,pdf --no-suptitle
python -m article_c.all_plot_compare --export-csv --output-dir article_c/plots/output/compare_all
```

### Usage conseillé

Utilisez ce pipeline si vous devez :

- reproduire des résultats de recherche ;
- générer des comparatifs détaillés ;
- produire un manifeste de figures et des diagnostics scientifiques.

## 3. Pipeline SFRD spécialisé

Le dossier `sfrd/` correspond à une CLI spécialisée, distincte de l’interface communauté `mobilesfrdth`.

### Workflow standard

```bash
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
