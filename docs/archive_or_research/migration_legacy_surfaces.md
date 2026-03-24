# Migration des anciennes surfaces (historique)

Ce document archive la transition vers la surface publique actuelle de LoRaFlexSim-2.

## Surfaces historiques concernées

- `mobilesfrdth`
- `sfrd/`
- `src/`
- `final/`

## Décision

Ces surfaces ne sont plus des points d’entrée publics.

La communication utilisateur doit se limiter à :

1. Dashboard : `panel serve loraflexsim/launcher/dashboard.py --show`
2. CLI : `loraflexsim`
3. Fallback : `python -m loraflexsim`

## Statut par élément

| Élément | Statut |
| --- | --- |
| `mobilesfrdth/` | conservé temporairement comme trace technique interne |
| `sfrd/` | retiré du parcours vivant |
| `src/` | retiré du parcours vivant |
| `final/` | retiré du parcours vivant |

## Règle documentaire

Toute mention de ces surfaces doit être explicitement marquée **historique**.
