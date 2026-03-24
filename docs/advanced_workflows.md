# Workflows avancés

Ce document couvre les flux hors parcours standard.

## Rappel

- **Parcours standard** : dashboard puis CLI `loraflexsim`.
- **Workflows avancés** : QoS spécialisé et reproductions de recherche.

## 1) QoS avancé

Utiliser `qos_cli/` uniquement pour des campagnes QoS expertes (balayages, comparaisons, rapports dédiés).

Point d’entrée habituel : `python -m qos_cli.lfs_run`.

## 2) Reproductions de recherche

Utiliser `pretest_campagne/` pour les scénarios de reproduction scientifique et comparatifs historiques.

## 3) Archives de migration

Les anciennes surfaces (`mobilesfrdth`, `sfrd`, `src`, `final`) sont sorties du parcours public et documentées comme historiques ici :

- `docs/archive_or_research/migration_legacy_surfaces.md`

Ne pas les présenter comme interfaces vivantes.
