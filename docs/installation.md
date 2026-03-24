# Installation (Windows 11 en priorité)

Ce guide décrit l’installation publique de LoRaFlexSim-2.

## Ce qui est officiel aujourd’hui

- **Principal** : dashboard Panel.
- **CLI supportée** : `loraflexsim`.
- **Fallback** : `python -m loraflexsim`.

Les surfaces `mobilesfrdth`, `sfrd/`, `src/` et `final/` sont historiques et ne doivent plus être utilisées comme entrée standard.

## Installation recommandée — Windows 11

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

## Vérification rapide

```powershell
loraflexsim --help
python -m loraflexsim --help
```

## Lancer le dashboard

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

Si le navigateur ne s’ouvre pas automatiquement, copiez l’URL affichée par Panel.

## Fallback Windows 11 (wrapper dépôt)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help
```

## Notes migration

- Les dossiers historiques retirés de l’usage public sont suivis dans `docs/archive_or_research/migration_legacy_surfaces.md`.
- Les workflows de recherche restent documentés séparément dans `docs/archive_or_research/`.
