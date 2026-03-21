# Référence de migration — `pretest_campagne/`

## Statut du document

- **Objectif** : figer le plan de renommage **avant toute modification de code**.
- **Portée** : dossiers, packages Python, chemins de résultats, chemins de figures, README, CLI et tests.
- **Règle de gouvernance** : **aucun renommage effectif ne doit commencer tant que cette table n'a pas été validée** par l'équipe responsable de la migration.
- **Principe** : utiliser une nomenclature uniforme, explicite et compatible Python/CLI, en `snake_case`.

## Décision cible

Le **nouveau dossier racine cible** de la migration est :

- `pretest_campagne/`

Ce nom devient la racine de référence pour toute campagne renommée ou réorganisée dans la migration.

## Conventions de nommage obligatoires

Les conventions suivantes s'appliquent partout pendant la migration :

- **`snake_case` obligatoire** pour les chemins, dossiers, modules Python, fichiers de sortie et identifiants de tests.
- **Aucune majuscule** dans les nouveaux chemins ou packages Python.
- **Aucun mélange de casse** (`pretest_campagne/iwcmc_archive`, `iwcmc`, `Article_C`, etc.) dans les nouveaux noms.
- Les noms doivent être **sémantiques**, **stables** et **réutilisables** dans la documentation, les imports et les scripts CLI.
- Quand un nom historique est trop générique (`article_a`, `article_b`, etc.), le nouveau nom doit rester court tout en explicitant son rôle dans la campagne.

## Table de renommage canonique

La table ci-dessous est la **source d'autorité** pour la migration. Toute implémentation doit s'y conformer.

| Ancien nom | Nouveau nom canonique | Type | Remarques |
| --- | --- | --- | --- |
| `article_a` | `scenario_a` | campagne | Campagne MNE3SD historique, renommée avec une nomenclature stable. |
| `article_b` | `scenario_b` | campagne | Campagne MNE3SD mobilité. |
| `pretest_campagne.scenario_c` | `scenario_c` | campagne | Pipeline de reproduction / recherche existant. |
| `article_d` | `scenario_d` | campagne | Campagne MNE3SD scénario D. |
| `pretest_campagne/iwcmc_archive` | `iwcmc_archive` | campagne / dossier | La casse historique est supprimée ; le statut archive est rendu explicite. |
| `iwcmc` | `iwcmc_archive` | préfixe de chemin | Tous les chemins `results/pretest_campagne/iwcmc_archive/...` deviennent `results/pretest_campagne/iwcmc_archive/...`. |

## Mapping obligatoire

Cette section doit être relue et validée **avant toute modification de code** pour éviter une migration partielle, incohérente ou non reproductible.

### 1. Packages Python

#### Packages de campagne

| Ancien package / module | Nouveau package / module cible |
| --- | --- |
| `pretest_campagne.scenario_c` | `pretest_campagne.scenario_c` |
| `pretest_campagne.scenario_c.common` | `pretest_campagne.scenario_c.common` |
| `pretest_campagne.scenario_c.step1` | `pretest_campagne.scenario_c.step1` |
| `pretest_campagne.scenario_c.step2` | `pretest_campagne.scenario_c.step2` |
| `pretest_campagne.scenario_c.tools` | `pretest_campagne.scenario_c.tools` |
| `pretest_campagne.iwcmc_archive.rl_static` | `pretest_campagne.iwcmc_archive.rl_static` |
| `pretest_campagne.iwcmc_archive.rl_mobile` | `pretest_campagne.iwcmc_archive.rl_mobile` |
| `pretest_campagne.iwcmc_archive.snir_static` | `pretest_campagne.iwcmc_archive.snir_static` |
| `pretest_campagne.scenario_a` | `pretest_campagne.scenario_a` |
| `pretest_campagne.scenario_b` | `pretest_campagne.scenario_b` |
| `pretest_campagne.scenario_d` | `pretest_campagne.scenario_d` |

#### Nouveaux packages Python importables

Les **nouveaux packages Python importables** à utiliser après migration sont donc :

- `pretest_campagne.scenario_a`
- `pretest_campagne.scenario_b`
- `pretest_campagne.scenario_c`
- `pretest_campagne.scenario_d`
- `pretest_campagne.iwcmc_archive`

Si des sous-packages communs sont mutualisés plus tard, ils devront rester sous le même préfixe racine :

- `pretest_campagne.common` *(optionnel, uniquement si une mutualisation réelle est décidée)*

### 2. Chemins de sortie `results/...`

#### Règle générale

Tous les résultats liés à cette migration doivent converger vers un espace de sortie homogène :

- `results/pretest_campagne/...`

#### Mapping minimal obligatoire

| Ancien chemin | Nouveau chemin cible |
| --- | --- |
| `results/pretest_campagne/scenario_a/...` | `results/pretest_campagne/scenario_a/...` |
| `results/pretest_campagne/scenario_b/...` | `results/pretest_campagne/scenario_b/...` |
| `results/pretest_campagne/scenario_d/...` | `results/pretest_campagne/scenario_d/...` |
| `pretest_campagne.scenario_c/step1/results/...` | `results/pretest_campagne/scenario_c/step1/...` |
| `pretest_campagne.scenario_c/step2/results/...` | `results/pretest_campagne/scenario_c/step2/...` |
| `results/pretest_campagne/iwcmc_archive/...` | `results/pretest_campagne/iwcmc_archive/...` |

#### Noms des nouveaux sous-dossiers de résultats

Les **nouveaux sous-dossiers de résultats** de premier niveau sont :

- `results/pretest_campagne/scenario_a/`
- `results/pretest_campagne/scenario_b/`
- `results/pretest_campagne/scenario_c/`
- `results/pretest_campagne/scenario_d/`
- `results/pretest_campagne/iwcmc_archive/`

### 3. Chemins `figures/...`

#### Règle générale

Toutes les figures liées aux campagnes renommées doivent être regroupées sous :

- `figures/pretest_campagne/...`

#### Mapping minimal obligatoire

| Ancien chemin | Nouveau chemin cible |
| --- | --- |
| `figures/pretest_campagne/scenario_a/...` | `figures/pretest_campagne/scenario_a/...` |
| `figures/pretest_campagne/scenario_b/...` | `figures/pretest_campagne/scenario_b/...` |
| `figures/pretest_campagne/scenario_d/...` | `figures/pretest_campagne/scenario_d/...` |
| `pretest_campagne.scenario_c/plots/output/...` | `figures/pretest_campagne/scenario_c/...` |
| `figures/pretest_campagne/iwcmc_archive/...` | `figures/pretest_campagne/iwcmc_archive/...` |
| `figures/pretest_campagne/iwcmc_archive/rl_static/...` | `figures/pretest_campagne/iwcmc_archive/rl_static/...` |
| `figures/pretest_campagne/iwcmc_archive/rl_mobile/...` | `figures/pretest_campagne/iwcmc_archive/rl_mobile/...` |
| `figures/pretest_campagne/iwcmc_archive/snir_static/...` | `figures/pretest_campagne/iwcmc_archive/snir_static/...` |

#### Noms des nouveaux sous-dossiers de figures

Les **nouveaux sous-dossiers de figures** de premier niveau sont :

- `figures/pretest_campagne/scenario_a/`
- `figures/pretest_campagne/scenario_b/`
- `figures/pretest_campagne/scenario_c/`
- `figures/pretest_campagne/scenario_d/`
- `figures/pretest_campagne/iwcmc_archive/`

### 4. README et commandes CLI

Tous les README, exemples de commandes et extraits CLI devront être migrés selon les règles suivantes :

| Ancien usage | Nouveau usage cible |
| --- | --- |
| `python -m pretest_campagne.scenario_c.run_all ...` | `python -m pretest_campagne.scenario_c.run_all ...` |
| `python -m pretest_campagne.scenario_c.make_all_plots ...` | `python -m pretest_campagne.scenario_c.make_all_plots ...` |
| `python -m pretest_campagne.scenario_a...` | `python -m pretest_campagne.scenario_a...` |
| `python -m pretest_campagne.scenario_b...` | `python -m pretest_campagne.scenario_b...` |
| `python -m pretest_campagne.scenario_d...` | `python -m pretest_campagne.scenario_d...` |
| `python -m pytest tests/pretest_campagne/iwcmc_archive` | `python -m pytest tests/pretest_campagne/iwcmc_archive` |

Règles supplémentaires :

- tous les exemples de chemins dans les README doivent pointer vers `results/pretest_campagne/...` ou `figures/pretest_campagne/...` ;
- aucune commande documentée ne doit mélanger ancien et nouveau nom dans la même ligne ;
- les chemins montrés dans la documentation doivent être identiques à ceux utilisés réellement dans le code et dans les tests.

### 5. Noms de tests et répertoires de tests

#### Répertoires de tests cibles

| Ancien répertoire | Nouveau répertoire cible |
| --- | --- |
| `tests/pretest_campagne.scenario_c/` | `tests/pretest_campagne/scenario_c/` |
| `tests/pretest_campagne/iwcmc_archive/` | `tests/pretest_campagne/iwcmc_archive/` |

#### Préfixes de noms de tests à harmoniser

| Ancien préfixe / nom | Nouveau préfixe / nom recommandé |
| --- | --- |
| `test_pretest_campagne.scenario_c_*` | `test_scenario_c_*` |
| `tests/pretest_campagne.scenario_c/test_*` | `tests/pretest_campagne/scenario_c/test_*` |
| `tests/pretest_campagne/iwcmc_archive/test_*` | `tests/pretest_campagne/iwcmc_archive/test_*` |
| références à `article_a` dans les tests | références à `scenario_a` |
| références à `article_b` dans les tests | références à `scenario_b` |
| références à `article_d` dans les tests | références à `scenario_d` |
| références à `pretest_campagne/iwcmc_archive` ou `iwcmc` dans les tests | références à `iwcmc_archive` |

## Règles de validation avant modification de code

Avant de renommer le moindre module, dossier ou import, vérifier les points suivants :

1. **Validation fonctionnelle de la table**
   - la table de renommage canonique est approuvée ;
   - aucun ancien nom n'est laissé sans cible explicite ;
   - aucune cible n'entre en conflit avec un package ou dossier existant.

2. **Validation technique**
   - tous les imports Python ont une cible de remplacement ;
   - tous les chemins `results/...` ont une cible de remplacement ;
   - tous les chemins `figures/...` ont une cible de remplacement ;
   - tous les README et commandes CLI ont une cible de remplacement ;
   - tous les tests et répertoires de tests ont une cible de remplacement.

3. **Validation de cohérence**
   - la casse est unifiée en `snake_case` ;
   - les nouveaux noms sont identiques dans le code, la documentation, les sorties et les tests ;
   - la migration peut être exécutée sans phase intermédiaire ambiguë où ancien et nouveau schéma coexistent partiellement.

## Check-list de pré-migration

- [ ] Valider le dossier racine cible `pretest_campagne/`.
- [ ] Valider les nouveaux noms `scenario_a`, `scenario_b`, `scenario_c`, `scenario_d`, `iwcmc_archive`.
- [ ] Valider les nouveaux packages importables `pretest_campagne.*`.
- [ ] Valider les nouveaux chemins `results/pretest_campagne/...`.
- [ ] Valider les nouveaux chemins `figures/pretest_campagne/...`.
- [ ] Valider la réécriture des README et commandes CLI.
- [ ] Valider la stratégie de renommage des tests.
- [ ] Confirmer qu'aucune modification de code ne commencera avant validation complète de cette table.

## Décision à figer avant implémentation

La migration devra être considérée comme **bloquée** tant que cette référence n'est pas explicitement validée. L'objectif est d'éviter :

- un renommage incomplet d'imports Python ;
- des sorties réparties entre anciens et nouveaux chemins ;
- des README incohérents avec les commandes réellement exécutables ;
- des tests cassés par un changement de nom partiel ;
- une coexistence durable de conventions de casse contradictoires.

En conséquence, **cette table fait foi** jusqu'à validation d'une version révisée du présent document.
