# Workflows avancés

Ce document regroupe les pipelines complets utiles après la prise en main initiale du projet.

## Positionnement rapide

Avant de basculer vers un workflow avancé, gardez la règle suivante :

- **Point d’entrée officiel recommandé** : `mobilesfrdth`
- **Points d’entrée avancés / spécialisés** : `sfrd`
- **Flux historiques / reproduction** : `final/`, `pretest_campagne/archive_or_mock/mobile-sfrd/`
- **Archives / anciens pipelines** : tout dossier déplacé sous l’espace d’archives

Autrement dit : **si `mobilesfrdth` suffit, restez sur `mobilesfrdth`**.

## Quand quitter le flux standard ?

Le flux standard reste le dashboard et la CLI `mobilesfrdth`. Basculez seulement si votre besoin correspond clairement à l’un des cas suivants :

- **Vers [`sfrd/`](../sfrd/README.md)** : quand vous devez lancer une **CLI avancée / spécialisée** pour des campagnes SFRD, de la calibration UCB ou une validation/agrégation spécifique non couverte par `mobilesfrdth`. Voir aussi la section [Pipeline SFRD spécialisé](#3-pipeline-sfrd-spécialisé).
- **Vers [`final/`](../final/README.md)** : quand vous devez rejouer un **pipeline historique d’export CSV/figures** avec des sorties attendues dans `final/data/` et `final/figures/`. Voir aussi la section [Pipeline historique d’export CSV/figures](#4-pipeline-historique-dexport-csvfigures).
- **Vers `pretest_campagne/archive_or_mock/mobile-sfrd/`** : seulement pour rejouer un **mock historique** conservé à des fins pédagogiques ou de comparaison légère. Voir aussi la section [Où trouver l’historique et les campagnes de recherche ?](#5-où-trouver-lhistorique-et-les-campagnes-de-recherche-).

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

### Rappel de gouvernance

Même si `sfrd` reste exécutable, **ce n’est pas la CLI principale recommandée pour un nouvel utilisateur**. Si vous lancez une nouvelle campagne standard et que vous n’avez pas besoin d’un pipeline SFRD identifié, revenez à `mobilesfrdth`.

## 4. Pipeline historique d’export CSV/figures

Le dossier [`final/`](../final/README.md) reste disponible pour un flux de reproduction simple centré sur les CSV et les figures.

### Quand y passer ?

Utilisez-le si vous avez déjà validé le flux standard et que vous devez ensuite :

- écrire rapidement un CSV de simulation dans `final/data/` ;
- produire des figures dans `final/figures/` avec les scripts historiques ;
- conserver une arborescence de sortie alignée avec d’anciens exports ou documents.

### Workflow Windows 11 recommandé

```powershell
python -m loraflexsim.run --nodes 30 --gateways 1 --mode random --interval 10 --steps 100 --output final/data/simulation.csv
python examples/analyse_resultats.py final/data/simulation.csv --output-dir final/figures --basename pdr_by_nodes
```

Pour les détails, voir directement [`final/README.md`](../final/README.md).

## 5. Où trouver l’historique et les campagnes de recherche ?

Les contenus hérités, de reproduction et d’archive sont maintenant regroupés sous `docs/archive_or_research/` et, pour les sources conservées dans l’arbre exécutable, sous `pretest_campagne/`.

### Statut de `mobile-sfrd`

`mobile-sfrd` n’est **pas** un outil encore supporté ni une entrée recommandée. Le dossier a été reclassé comme **archive d’un mock pédagogique historique** et déplacé sous `pretest_campagne/archive_or_mock/mobile-sfrd/`.

Utilisez-le uniquement si vous devez :

- illustrer un mock déterministe très léger ;
- rejouer les cinq expériences simplifiées qu’il produit ;
- comparer un artefact pédagogique avec le flux standard.

Ne l’utilisez pas pour une campagne standard, une validation produit ou un workflow communauté. Dans ces cas, l’entrée officielle reste `mobilesfrdth`.
