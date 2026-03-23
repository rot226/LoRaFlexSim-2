# Workflows avancés

Ce document regroupe les pipelines complets utiles après la prise en main initiale du projet.

## Positionnement rapide

Avant de basculer vers un workflow avancé, gardez la règle suivante :

- **Point d’entrée officiel recommandé** : `loraflexsim`
- **Points d’entrée avancés / spécialisés** : `qos_cli`, `pretest_campagne`
- **Flux historiques / reproduction** : `pretest_campagne/`, `docs/archive_or_research/`, `pretest_campagne/archive_or_mock/mobile-sfrd/`
- **Archives / anciens pipelines** : tout dossier déplacé sous l’espace d’archives

Autrement dit : **si `loraflexsim` suffit, restez sur `loraflexsim`**.

## Quand quitter le flux standard ?

Le flux standard reste le dashboard et la CLI `loraflexsim`. Basculez seulement si votre besoin correspond clairement à l’un des cas suivants :

- **Vers `docs/archive_or_research/sfrd_legacy.md`** : si vous devez relire la documentation d’un ancien pipeline SFRD désormais retiré du dépôt exécutable.
- **Vers `docs/archive_or_research/final_legacy.md`** : si vous devez consulter l’ancien pipeline d’export CSV/figures conservé uniquement comme archive documentaire.
- **Vers `pretest_campagne/archive_or_mock/mobile-sfrd/`** : seulement pour rejouer un **mock historique** conservé à des fins pédagogiques ou de comparaison légère. Voir aussi la section [Où trouver l’historique et les campagnes de recherche ?](#4-où-trouver-lhistorique-et-les-campagnes-de-recherche-).

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

## 3. Archives de pipelines retirés

Les anciens pipelines `sfrd/` et `final/` ont été retirés de l’arbre exécutable. Leur valeur résiduelle est désormais documentaire uniquement.

### Où retrouver leur contexte ?

- `docs/archive_or_research/sfrd_legacy.md` : description de l’ancienne CLI SFRD, de ses cas d’usage et de ses commandes historiques.
- `docs/archive_or_research/final_legacy.md` : description du pipeline historique d’export CSV/figures et des sorties autrefois produites.

### Que faire aujourd’hui à la place ?

- Pour une campagne reproductible moderne : utilisez `loraflexsim run`, puis `loraflexsim aggregate`, `loraflexsim plots` et `loraflexsim validate`.
- Pour la recherche et les reproductions enrichies : utilisez `pretest_campagne/` et les guides de `docs/archive_or_research/`.
- Pour le moteur historique bas niveau : utilisez `python -m loraflexsim.run` si vous avez une contrainte technique spécifique.

## 4. Où trouver l’historique et les campagnes de recherche ?

Les contenus hérités, de reproduction et d’archive sont maintenant regroupés sous `docs/archive_or_research/` et, pour les sources conservées dans l’arbre exécutable, sous `pretest_campagne/`.

### Statut de `mobile-sfrd`

`mobile-sfrd` n’est **pas** un outil encore supporté ni une entrée recommandée. Le dossier a été reclassé comme **archive d’un mock pédagogique historique** et déplacé sous `pretest_campagne/archive_or_mock/mobile-sfrd/`.

Utilisez-le uniquement si vous devez :

- illustrer un mock déterministe très léger ;
- rejouer les cinq expériences simplifiées qu’il produit ;
- comparer un artefact pédagogique avec le flux standard.

Ne l’utilisez pas pour une campagne standard, une validation produit ou un workflow communauté. Dans ces cas, l’entrée officielle reste `loraflexsim`.
