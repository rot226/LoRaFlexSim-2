# Campagnes de brouillage mobilesfrdth

Cette extension ajoute un sous-package `mobilesfrdth.jamming` dédié à la préparation de campagnes de brouillage LoRa/LoRaWAN. Elle s'intègre au package Python `mobilesfrdth` et conserve les points d'entrée existants : les fichiers `mobilesfrdth/simulator/engine.py`, `mobilesfrdth/simulator/io.py` et `mobilesfrdth/cli.py` ne sont ni déplacés ni renommés.

> Note de compatibilité : certaines commandes historiques ou consignes de reproduction peuvent encore mentionner `loraflexsim`. Dans ce dépôt, l'extension de brouillage décrite ici cible bien `mobilesfrdth` ; utilisez donc les imports `mobilesfrdth.jamming` pour les campagnes Python.

## API publique stable

Le module `mobilesfrdth.jamming.__init__` expose uniquement des adaptateurs stables :

- `Jammer`, `JammerConfig` et `JammerObservation` pour représenter les brouilleurs et leurs observations radio.
- `JammerScheduler`, `JammerWindow` et `periodic_windows` pour planifier des fenêtres d'activation.
- `grid_placement` et `random_placement` pour générer des positions reproductibles.
- `fixed_channels`, `round_robin_channel` et `random_channel` pour sélectionner les canaux ciblés.
- `JammingScenario`, `JammingCampaign` et `build_campaign` pour composer des campagnes.
- `JammingMetrics`, `summarize_jamming` et `export_jamming_rows` pour agréger et exporter les résultats.

## Exemple minimal

```python
from mobilesfrdth.jamming import build_campaign, summarize_jamming

campaign = build_campaign(
    name="smoke_jamming",
    jammer_counts=(0, 1, 3),
    area_size_m=1_000.0,
    placement="grid",
)

metrics = summarize_jamming(jammed_flags=[False, True, True])
print(campaign.name, metrics.jammed_ratio)
```

## Intégration recommandée

1. Générez les scénarios de base avec les outils `mobilesfrdth` existants.
2. Construisez une `JammingCampaign` séparée pour décrire les brouilleurs à injecter.
3. Joignez les métadonnées de brouillage aux résultats de simulation sans modifier les chemins historiques du simulateur.
4. Exportez les métriques additionnelles via `export_jamming_rows` afin de garder les CSV de campagne lisibles sous Windows 11, PowerShell ou les environnements Unix.
