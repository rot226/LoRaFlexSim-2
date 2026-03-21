# Archive IWCMC

Documentation historique issue de `IWCMC/README.md`.

## Portée

Ce contenu documente les campagnes héritées conservées pour reproduction et comparaison :

- `snir_static/`
- `rl_static/`
- `rl_mobile/`
- `MED/`
- `archive/`

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
4. Vérifier puis archiver les sorties.

## Vérification

```powershell
python -m pytest IWCMC/tests
```

## But de cette archive

Ce contenu n’est pas nécessaire pour un premier usage. Il sert surtout à conserver la structure historique des campagnes et à rejouer des expériences héritées.
