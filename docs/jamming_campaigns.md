# Campagnes de brouillage LoRaFlexSim / mobilesfrdth

## Objectif du module

Le module `mobilesfrdth.jamming` sert à préparer, exécuter et agréger des campagnes de brouillage LoRa/LoRaWAN reproductibles. Il ajoute des brouilleurs, leurs fenêtres d'émission et des exports CSV spécialisés autour du simulateur existant, sans inclure le trafic des brouilleurs dans les métriques de trafic légitime. Le point d'entrée recommandé pour ces campagnes est la CLI de brouillage exposée par `python -m mobilesfrdth jamming ...`; `python -m loraflexsim.cli ...` reste un adaptateur de compatibilité pour les commandes historiques.

## Scénarios documentés

### `baseline_jamming_single_channel`

Scénario témoin brouillé sur un seul canal EU868 :

- trafic légitime limité à `868.1 MHz` ;
- canal brouillé : `868.1 MHz` ;
- 6 brouilleurs placés sur un cercle de rayon `10 m` autour de la gateway ;
- sélection de canal `static` ;
- scénario adapté aux comparaisons simples entre un réseau mono-canal non brouillé et brouillé.

Le fichier de configuration fourni le plus proche est `config/jamming/baseline_single_channel.yaml`. Pour conserver le nom long dans les sorties, passez explicitement `--scenario baseline_jamming_single_channel` ou surchargez la clé `scenario`.

### `multichannel_jamming_adr_channel_selection`

Scénario multicanal EU868 avec sélection de canal assistée par ADR :

- trafic légitime réparti sur le plan EU868 par défaut ;
- canal brouillé par défaut : `868.1 MHz` ;
- 6 brouilleurs placés sur un cercle de rayon `10 m` autour de la gateway ;
- sélection de canal `adr-assisted` ;
- ADR activé par défaut afin d'étudier la capacité de réaffectation canal/SF quand un canal est perturbé.

Le fichier de configuration fourni le plus proche est `config/jamming/multichannel_adr_selection.yaml`. Pour conserver le nom long dans les sorties, passez explicitement `--scenario multichannel_jamming_adr_channel_selection` ou surchargez la clé `scenario`.

## Paramètres par défaut EU868

| Paramètre | Valeur par défaut |
| --- | --- |
| Bande | `EU868` |
| Canaux EU868 multicanal | `868.1`, `868.3`, `868.5`, `867.1`, `867.3`, `867.5`, `867.7`, `867.9 MHz` |
| Canal mono-canal / canal brouillé par défaut | `868.1 MHz` (`868100000 Hz`) |
| Durée simulée | `3600 s` |
| Nombres de nœuds autorisés pour les scénarios prédéfinis | `20`, `50`, `100` |
| Seeds de campagne dans les fichiers YAML | `0:49` |
| Position gateway | `(0.0 m, 0.0 m)` |
| Distribution des nœuds | uniforme, zone `1000 m x 1000 m` dans les YAML ; disque de rayon `1000 m` dans le runner événementiel |
| SF initiaux | tirage aléatoire de `SF7` à `SF12` |
| Puissance TX nœuds légitimes | `14 dBm` |
| Puissance TX brouilleurs | `14 dBm` |
| Bande passante | `125 kHz` |
| Intervalle d'envoi applicatif | uniforme entre `150 s` et `200 s` dans les scénarios prédéfinis |
| Duty-cycle brouilleur YAML | `0.01` |
| Taille des bins temporels | `60 s` |
| ADR baseline | `off` |
| ADR multicanal | `on` |

## Métriques exportées et CSV produits

Un run écrit par défaut une arborescence contenant `raw/`, `per_run/` et `config_used.yaml`.

| Fichier | Contenu principal |
| --- | --- |
| `per_run/run_summary.csv` | synthèse du run : scénario, nœuds, ADR, seed, durée, nombre de paquets légitimes, paquets reçus/perdus/brouillés, PDR, nombre de fenêtres de brouillage et description des fenêtres. |
| `raw/packet_events_<scenario>_n<nodes>_adr_<on-off>_seed_<seed>.csv` | événements paquet légitimes enrichis : `packet_id`, temps, nœud, gateway, `sf`, fréquence, canal, puissance TX, payload, airtime, états `sent`, `received`, `lost`, `collided`, `jammed`, délai. |
| `raw/node_metrics_<scenario>_n<nodes>_adr_<on-off>_seed_<seed>.csv` | métriques par nœud : envoyés, reçus, perdus, collisions, brouillés, PDR, ratio brouillé, délai moyen. |
| `raw/channel_timeseries_<scenario>_n<nodes>_adr_<on-off>_seed_<seed>.csv` | série temporelle agrégée par canal : envoyés, reçus, perdus, brouillés. |
| `raw/sf_timeseries_<scenario>_n<nodes>_adr_<on-off>_seed_<seed>.csv` | série temporelle agrégée par spreading factor : envoyés, reçus, perdus, brouillés. |
| CSV d'agrégation, par exemple `results/jamming/summary.csv` | agrégation récursive des `run_summary.csv` par scénario, nombre de nœuds, ADR et politique de canal : `seeds_count`, moyennes, écarts types et IC95 du PDR quand disponible. |

Le PDR des exports de run correspond aux paquets légitimes reçus divisés par les paquets légitimes envoyés. Dans le calcul utilitaire `compute_packet_metrics`, le PDR utilise explicitement les paquets légitimes uniques reçus : les réceptions dupliquées augmentent `rx_packets_total`, mais un même `packet_id` ne compte qu'une seule fois dans `rx_unique_packets_total` et donc dans `pdr_percent`.

Les paquets, fenêtres ou émissions des brouilleurs ne sont jamais inclus dans les métriques de trafic légitime. Les événements bruts exportés par le runner ne contiennent que les paquets légitimes enrichis par les indicateurs de brouillage ; les informations brouilleur sont conservées séparément dans le résumé (`jamming_windows`, `jamming_window_count`) et dans la configuration utilisée.

## Commandes Windows 11

Les exemples suivants supposent que vous êtes à la racine du dépôt et que l'environnement Python du projet est activé.

### Run unique

PowerShell :

```powershell
python -m mobilesfrdth jamming run `
  --config config\jamming\baseline_single_channel.yaml `
  --scenario baseline_jamming_single_channel `
  --nodes 20 `
  --adr off `
  --seed 0 `
  --sim-time 3600 `
  --channels 868.1 `
  --jammed-channel 868.1 `
  --channel-selection static `
  --time-bin-size 60 `
  --out results\jamming\baseline_single_run `
  --overwrite
```

CMD :

```cmd
python -m mobilesfrdth jamming run ^
  --config config\jamming\baseline_single_channel.yaml ^
  --scenario baseline_jamming_single_channel ^
  --nodes 20 ^
  --adr off ^
  --seed 0 ^
  --sim-time 3600 ^
  --channels 868.1 ^
  --jammed-channel 868.1 ^
  --channel-selection static ^
  --time-bin-size 60 ^
  --out results\jamming\baseline_single_run ^
  --overwrite
```

### Campagne complète mono-canal

PowerShell :

```powershell
python -m mobilesfrdth jamming campaign `
  --config config\jamming\baseline_single_channel.yaml `
  --scenario baseline_jamming_single_channel `
  --nodes 20 `
  --adr off `
  --seeds 0:49 `
  --sim-time 3600 `
  --channels 868.1 `
  --jammed-channel 868.1 `
  --channel-selection static `
  --time-bin-size 60 `
  --out results\jamming\baseline_campaign `
  --resume
```

CMD :

```cmd
python -m mobilesfrdth jamming campaign ^
  --config config\jamming\baseline_single_channel.yaml ^
  --scenario baseline_jamming_single_channel ^
  --nodes 20 ^
  --adr off ^
  --seeds 0:49 ^
  --sim-time 3600 ^
  --channels 868.1 ^
  --jammed-channel 868.1 ^
  --channel-selection static ^
  --time-bin-size 60 ^
  --out results\jamming\baseline_campaign ^
  --resume
```

### Campagne multicanal

PowerShell :

```powershell
python -m mobilesfrdth jamming campaign `
  --config config\jamming\multichannel_adr_selection.yaml `
  --scenario multichannel_jamming_adr_channel_selection `
  --nodes 20 `
  --adr on `
  --seeds 0:49 `
  --sim-time 3600 `
  --channels 868.1,868.3,868.5,867.1,867.3,867.5,867.7,867.9 `
  --jammed-channel 868.1 `
  --channel-selection adr-assisted `
  --time-bin-size 60 `
  --out results\jamming\multichannel_campaign `
  --resume
```

CMD :

```cmd
python -m mobilesfrdth jamming campaign ^
  --config config\jamming\multichannel_adr_selection.yaml ^
  --scenario multichannel_jamming_adr_channel_selection ^
  --nodes 20 ^
  --adr on ^
  --seeds 0:49 ^
  --sim-time 3600 ^
  --channels 868.1,868.3,868.5,867.1,867.3,867.5,867.7,867.9 ^
  --jammed-channel 868.1 ^
  --channel-selection adr-assisted ^
  --time-bin-size 60 ^
  --out results\jamming\multichannel_campaign ^
  --resume
```

### Agrégation seule

PowerShell :

```powershell
python -m mobilesfrdth jamming aggregate `
  --input results\jamming\multichannel_campaign `
  --output results\jamming\multichannel_summary.csv
```

CMD :

```cmd
python -m mobilesfrdth jamming aggregate ^
  --input results\jamming\multichannel_campaign ^
  --output results\jamming\multichannel_summary.csv
```

### Dry-run

PowerShell :

```powershell
python -m mobilesfrdth jamming campaign `
  --config config\jamming\multichannel_adr_selection.yaml `
  --scenario multichannel_jamming_adr_channel_selection `
  --nodes 20 `
  --adr on `
  --seeds 0:2 `
  --sim-time 3600 `
  --channels 868.1,868.3,868.5,867.1,867.3,867.5,867.7,867.9 `
  --jammed-channel 868.1 `
  --channel-selection adr-assisted `
  --time-bin-size 60 `
  --out results\jamming\dry_run_preview `
  --dry-run
```

CMD :

```cmd
python -m mobilesfrdth jamming campaign ^
  --config config\jamming\multichannel_adr_selection.yaml ^
  --scenario multichannel_jamming_adr_channel_selection ^
  --nodes 20 ^
  --adr on ^
  --seeds 0:2 ^
  --sim-time 3600 ^
  --channels 868.1,868.3,868.5,867.1,867.3,867.5,867.7,867.9 ^
  --jammed-channel 868.1 ^
  --channel-selection adr-assisted ^
  --time-bin-size 60 ^
  --out results\jamming\dry_run_preview ^
  --dry-run
```

## Adaptateur `loraflexsim.cli` : usage et limites

`loraflexsim.cli` est une façade de compatibilité qui délègue directement à la CLI de brouillage canonique. Les commandes équivalentes sont donc possibles avec `python -m loraflexsim.cli run`, `python -m loraflexsim.cli campaign` et `python -m loraflexsim.cli aggregate`.

Limites à garder en tête :

- l'adaptateur ne fournit pas une CLI générale pour tout LoRaFlexSim ; il cible les campagnes de brouillage ;
- `campaign` est un alias de campagne de brouillage, pas un orchestrateur universel de scénarios historiques ;
- les imports Python stables restent ceux de `mobilesfrdth.jamming` ;
- la fusion YAML/CLI ne renseigne que les options connues par la CLI (`scenario`, `nodes`, `adr`, `seeds`, `channels`, `jammed_channel`, etc.) ; les clés de documentation comme `band`, `gateway_position` ou `node_distribution` peuvent être conservées dans `config_used.yaml`, mais ne modifient pas automatiquement tous les paramètres internes du runner si aucune option CLI correspondante n'existe ;
- une sélection de canal dynamique sans ADR est bloquée par défaut : il faut soit activer `--adr on`, soit ajouter explicitement `--allow-channel-selection-without-adr` ;
- `--export-raw-events` est un booléen d'activation : en l'état, les exports standard écrivent les CSV principaux du run, et l'option sert surtout à documenter l'intention dans la configuration fusionnée.
