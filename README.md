# LoRaFlexSim-2

LoRaFlexSim-2 est un simulateur LoRa/LoRaWAN en Python pour exécuter des campagnes, agréger des résultats et visualiser les métriques réseau.

## Parcours public recommandé

1. **Voie principale** : dashboard Panel.
2. **Voie scriptable** : CLI `loraflexsim`.
3. **Fallback technique** : `python -m loraflexsim`.

Les anciens noms et anciennes surfaces (`mobilesfrdth`, `sfrd/`, `src/`, `final/`) ne font plus partie du parcours public.

## Démarrage rapide (Windows 11)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --no-build-isolation
```

### Lancer le dashboard (recommandé)

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

### Utiliser la CLI (si besoin d’automatiser)

```powershell
loraflexsim --help
loraflexsim presets --list
loraflexsim run --preset paper_fast --out runs/quickstart
```

### Fallback sans entrypoint console

```powershell
powershell -ExecutionPolicy Bypass -File scripts/loraflexsim.ps1 --help
python -m loraflexsim --help
```

## Dossiers actifs vs historiques

| Zone | Statut | Usage |
| --- | --- | --- |
| `loraflexsim/` | actif | moteur, dashboard, CLI publique |
| `docs/` | actif | documentation utilisateur |
| `scripts/` | actif | bootstrap et automatisation |
| `qos_cli/` | spécialisé | campagnes QoS expertes |
| `docs/archive_or_research/` | historique | mémoire de migration et recherche |
| `pretest_campagne/` | historique/recherche | reproductions et comparatifs |

## Suppressions / migration

- `sfrd/`, `src/` et `final/` : retirés de la surface vivante.
- `mobilesfrdth/` : conservé uniquement comme trace interne de migration, documentée comme historique.
- Détails : `docs/archive_or_research/migration_legacy_surfaces.md`.
