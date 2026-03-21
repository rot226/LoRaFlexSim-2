# Archive métier `iwcmc_archive`

Documentation historique issue de `pretest_campagne/iwcmc_archive/README.md`.

## Portée

Ce contenu documente les campagnes héritées conservées pour reproduction et comparaison dans l’archive métier `iwcmc_archive` :

- `pretest_campagne/iwcmc_archive/snir_static/`
- `pretest_campagne/iwcmc_archive/rl_static/`
- `pretest_campagne/iwcmc_archive/rl_mobile/`
- `pretest_campagne/iwcmc_archive/MED/`
- `pretest_campagne/iwcmc_archive/archive/`

## Structure type des campagnes

Chaque campagne suit en général la structure suivante :

```text
modules/   # utilitaires et helpers
scenarios/ # scripts de lancement
plots/     # scripts de génération
figures/   # exports PNG/SVG/PDF
data/      # CSV et données intermédiaires
```

## Dépendances

- Python ≥ 3.10
- `pip`
- bibliothèques usuelles : `pandas`, `matplotlib`

## Phases de travail

1. Préparer l’environnement.
2. Exécuter les scénarios.
3. Générer les graphiques.
4. Vérifier puis archiver les sorties sous `results/pretest_campagne/iwcmc_archive/`.

## Vérification

Depuis Windows 11 / PowerShell, exécutez la commande suivante depuis la racine du dépôt :

```powershell
python -m pytest tests/pretest_campagne/iwcmc_archive
```

## But de cette archive

Ce contenu n’est pas nécessaire pour un premier usage. Il sert surtout à conserver la structure historique des campagnes et à rejouer des expériences héritées sous le nom métier `iwcmc_archive`.
