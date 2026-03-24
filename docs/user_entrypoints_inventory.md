# Inventaire des points d’entrée utilisateur

## Entrées publiques actuelles

| Entrée | Statut | Usage |
| --- | --- | --- |
| `panel serve loraflexsim/launcher/dashboard.py --show` | principale | usage interactif |
| `loraflexsim` | officielle | campagnes CLI |
| `python -m loraflexsim` | fallback | exécution Python directe |
| `scripts/loraflexsim.ps1` | wrapper Windows 11 | fallback local |
| `scripts/loraflexsim.sh` | wrapper Linux/macOS | fallback local |

## Entrées non publiques (historique / expert)

| Zone | Statut |
| --- | --- |
| `python -m loraflexsim.run` | technique/historique |
| `qos_cli/` | spécialisé |
| `pretest_campagne/` | recherche |
| `docs/archive_or_research/` | archive documentaire |

## Surfaces retirées du récit public

- `mobilesfrdth`
- `sfrd/`
- `src/`
- `final/`

Traçabilité de la migration : `docs/archive_or_research/migration_legacy_surfaces.md`.
