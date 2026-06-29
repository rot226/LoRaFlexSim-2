# Résultats des campagnes de brouillage

Ce dossier est le point de chute recommandé pour les sorties produites par les campagnes de brouillage LoRaFlexSim. Les fichiers volumineux générés par les exécutions ne sont pas versionnés : conservez dans Git uniquement cette documentation et, si nécessaire, de petits fichiers de consigne.

## Arborescence produite

Une campagne ou un run de brouillage peut produire l'arborescence suivante sous `results/jamming/` ou sous un sous-dossier de campagne :

```text
results/jamming/
├── README.md
├── config_used.yaml
├── commands.txt
├── logs/
├── raw/
├── per_run/
└── aggregate/
```

- `config_used.yaml` : copie normalisée de la configuration effectivement utilisée pour lancer le run ou la campagne. Elle sert à vérifier les paramètres après fusion entre fichier YAML/JSON et options CLI.
- `commands.txt` : journal manuel ou généré des commandes lancées pour reproduire la campagne, par exemple les invocations `loraflexsim ...` exactes.
- `logs/` : journaux d'exécution, traces standard output/error et diagnostics de batch. Ce dossier peut grossir rapidement et reste ignoré par Git.
- `raw/` : exports bruts par run, notamment les événements paquets, métriques par nœud et séries temporelles par canal ou spreading factor. Ces CSV peuvent être volumineux et ne doivent pas être commités.
- `per_run/` : métriques résumées au niveau run, dont `run_summary.csv`, utilisées comme entrée pour l'agrégation de campagne.
- `aggregate/` : sorties agrégées multi-runs ou multi-seeds, comme `campaign_summary.csv` et les tableaux destinés à l'analyse.

## Bonnes pratiques

- Lancez les essais locaux dans un sous-dossier dédié, par exemple `results/jamming/baseline_smoke/`, afin de séparer les campagnes.
- Pour les tests automatisés, utilisez toujours un répertoire temporaire fourni par `tmp_path` plutôt que `results/jamming/`. Les tests existants de l'export CSV, de l'agrégation et de la CLI jamming écrivent leurs sorties dans `tmp_path`, ce qui évite de polluer ce dossier de résultats.
- Ne versionnez pas les CSV, logs, captures brutes ou artefacts lourds générés par les simulations ; archivez-les en dehors du dépôt si vous devez les partager.
