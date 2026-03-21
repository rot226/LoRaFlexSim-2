# Reproduction du pipeline scénario C

Documentation historique / de recherche issue de `pretest_campagne/scenario_c/README.md`.

## Organisation

- `pretest_campagne/scenario_c/common/` : modules utilitaires partagés ;
- `pretest_campagne/scenario_c/step1/` : scripts de la première étape ;
- `pretest_campagne/scenario_c/step2/` : scripts de la seconde étape ;
- `pretest_campagne/scenario_c/run_all.py` : exécution complète ;
- `pretest_campagne/scenario_c/make_all_plots.py` : génération de graphes.

## Contrat de sortie

Exécutez le pipeline depuis la racine du dépôt sous Windows 11 / PowerShell afin de conserver des chemins relatifs cohérents.

### Sorties fines

- `results/pretest_campagne/scenario_c/step1/by_size/size_<N>/rep_<R>/...`
- `results/pretest_campagne/scenario_c/step2/by_size/size_<N>/rep_<R>/...`

### Agrégats

- `results/pretest_campagne/scenario_c/step1/aggregates/aggregated_results.csv`
- `results/pretest_campagne/scenario_c/step2/aggregates/aggregated_results.csv`

## Workflow Windows 11

```powershell
python -m pretest_campagne.scenario_c.run_all --network-sizes 80 160 320 640 1280 --replications 5 --seeds_base 1
python -m pretest_campagne.scenario_c.tools.aggregate_step1
python -m pretest_campagne.scenario_c.tools.aggregate_step2
python -m pretest_campagne.scenario_c.make_all_plots --formats png,eps,pdf --no-suptitle
```

## Modèle radio et SNIR

Le pipeline scénario C documente un proxy radio reproductible avec :

- un modèle de collisions simplifié ;
- un mode SNIR OFF basé sur les seuils de sensibilité ;
- un mode SNIR ON avec interférences co-SF sur le même canal ;
- des seuils SNIR assouplis via des bornes configurables.

## Pourquoi ce document est dans archive_or_research

Ce pipeline est surtout utile pour la reproduction d’expériences, la génération de figures de recherche et l’analyse détaillée. Il n’est pas nécessaire pour un premier usage communautaire.
