# `pretest_campagne/iwcmc_archive/`

## En 30 secondes

| Rubrique | Réponse rapide |
| --- | --- |
| **À quoi sert ce dossier ?** | Conserver les campagnes héritées `iwcmc_archive` pour reproduction, comparaison et archivage métier. |
| **Quand l’utiliser ?** | Quand vous devez rejouer ou relire une campagne historique `snir_static`, `rl_static`, `rl_mobile` ou les artefacts MED. |
| **Quand ne pas l’utiliser ?** | Ne l’utilisez pas pour une nouvelle campagne standard ni comme point d’entrée principal du projet. |
| **Point d’entrée principal** | Commencer par la documentation d’archive, puis utiliser les scripts `run_campaign.*` des sous-dossiers concernés. |
| **Sorties produites** | Des résultats historiques dans `results/pretest_campagne/iwcmc_archive/` et des artefacts d’archive spécifiques à chaque sous-campagne. |
| **Documentation détaillée** | `docs/archive_or_research/iwcmc_archive.md` et `docs/archive_or_research/README.md`. |

**Documentation historique** — ce dossier est conservé pour les campagnes héritées, la reproduction et la comparaison de résultats.

## Documentation détaillée

### Objectif du dossier

Le dossier `pretest_campagne/iwcmc_archive/` sert de point d’entrée court vers les artefacts et la documentation de l’archive métier `iwcmc_archive`.

### Prérequis

- **OS documenté en priorité : Windows 11**.
- **Shell documenté : PowerShell**.
- **Répertoire d’exécution : racine du dépôt**.
- **Version Python recommandée : 3.11**.
- **Support packaging : Python 3.11 à 3.12**.
- **Installation standard recommandée :** `python -m pip install -e . --no-build-isolation` après activation du venv.
- **`PYTHONPATH=src` n’est pas requis** pour le flux standard ; il ne s’applique qu’aux contournements offline/fallback explicitement indiqués ailleurs.

### Scénario minimal

Pour un usage minimal, commencez par lire la documentation d’archive afin d’identifier la campagne et les scripts correspondants.

### Commandes de run

Aucune commande de run unique n’est maintenue dans ce README ; utilisez les scripts `run_campaign.ps1` ou `run_campaign.sh` du sous-dossier concerné.

### Lien direct vers la doc détaillée

- `docs/archive_or_research/iwcmc_archive.md`
- `docs/archive_or_research/README.md`
