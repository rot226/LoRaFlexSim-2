# Guide utilisateur — CLI `loraflexsim`

La CLI publique qui subsiste est **`loraflexsim`**.

## Quand utiliser la CLI ?

Utilisez la CLI si vous devez automatiser des campagnes reproductibles. Sinon, commencez par le dashboard.

## Vérifier la disponibilité (Windows 11)

```powershell
loraflexsim --help
python -m loraflexsim --help
```

## Workflow standard

```powershell
loraflexsim presets --list
loraflexsim run --preset paper_fast --out runs/quickstart
loraflexsim aggregate --results runs/quickstart --out runs/quickstart
loraflexsim plots --aggregates-dir runs/quickstart/aggregates --out runs/quickstart/plots --profile exploratory
loraflexsim validate --aggregates-dir runs/quickstart/aggregates
```

## Fallbacks Windows 11

```powershell
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help
python -m loraflexsim --help
```

## Positionnement officiel

- **Dashboard** : voie principale pour découvrir le projet.
- **CLI `loraflexsim`** : voie officielle pour l’automatisation.
- **Anciens espaces (`mobilesfrdth`, `sfrd`, `src`, `final`)** : historiques uniquement.

Référence migration : `docs/archive_or_research/migration_legacy_surfaces.md`.
