# `pretest_campagne/scenario_a/`

## En 30 secondes

| Rubrique | Réponse rapide |
| --- | --- |
| **À quoi sert ce dossier ?** | Regrouper les scripts et figures du scénario A de la campagne MNE3SD, centrés sur densité, charge et profils énergétiques. |
| **Quand l’utiliser ?** | Quand vous devez rejouer ou ajuster les expériences du scénario A et régénérer les CSV/figures associés. |
| **Quand ne pas l’utiliser ?** | Ne l’utilisez pas pour une campagne standard `mobilesfrdth` ni pour un autre scénario MNE3SD. |
| **Point d’entrée principal** | Les modules de `pretest_campagne.scenario_a.scenarios` et le batch `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_a`. |
| **Sorties produites** | Des CSV dans `results/mne3sd/scenario_a/` et des figures dans `figures/mne3sd/scenario_a/`. |
| **Documentation détaillée** | Ce README détaille les modules, paramètres et commandes ; voir aussi `docs/energy_profiles.md` pour la partie énergie. |

## Documentation détaillée

### Objectifs

- Reproduire les simulations nécessaires au scénario A de la campagne MNE3SD.
- Regrouper en un seul endroit les définitions de scénarios et les utilitaires réutilisables partagés dans l'étude.
- Collecter les métriques propres à chaque scénario sous forme de fichiers CSV et les post-traiter en figures prêtes pour la publication.

### Paramètres de simulation communs

Chaque script de scénario expose un ensemble cohérent d'options en ligne de commande pour faciliter la reproductibilité :

- `--config` : chemin d'un fichier de configuration optionnel pour la simulation, qui remplace les valeurs par défaut fournies avec le dépôt.
- `--seed` : graine aléatoire de base appliquée au simulateur. Les scripts peuvent en dériver d'autres graines.
- `--runs` : nombre de répétitions Monte Carlo à exécuter pour chaque configuration de scénario.
- `--duration` : durée de la simulation en secondes. Si l'option est absente, chaque script revient à sa valeur par défaut documentée.
- `--output` : fichier CSV de destination. Par convention il est placé dans `results/mne3sd/scenario_a/`.

Les scripts de `plots/` suivent la même logique :

- `--input` : un ou plusieurs fichiers CSV produits par les scripts de scénario.
- `--figures-dir` : dossier où les figures générées seront écrites. Valeur par défaut : `figures/mne3sd/scenario_a/`.
- `--format` : format d'image pour les graphiques exportés (par ex. `png`, `pdf`, `svg`).

### Profils d'exécution

Tous les lanceurs de scénarios acceptent l'option commune `--profile` (ou la variable d'environnement `MNE3SD_PROFILE`) pour basculer entre des presets :

- `full` *(valeur par défaut)* – conserve les paramètres de publication décrits dans chaque script.
- `fast` – limite le nombre de nœuds à 150 et réduit le volume de paquets/répétitions pour accélérer les itérations locales. C'est le réglage conseillé pour des itérations rapides sous Windows 11.
- `ci` – réduit le nombre de nœuds, de répétitions et l'étendue des paramètres explorés afin d'accélérer les tests automatisés et les vérifications rapides, tout en exerçant l'intégralité de la chaîne.

### Arborescence et artefacts

```text
pretest_campagne/scenario_a/
├── README.md
├── scenarios/
└── plots/
```

### Sorties CSV

Toutes les métriques brutes ou agrégées produites par les expériences doivent être stockées dans `results/mne3sd/scenario_a/`.

### Figures

Utilisez `figures/mne3sd/scenario_a/` pour stocker toute figure exportée pour le scénario A.

### Générer les données de simulation

```powershell
python -m pretest_campagne.scenario_a.scenarios.<scenario_module> `
    --runs 10 `
    --duration 3600 `
    --seed 42 `
    --output results/mne3sd/scenario_a/<scenario_name>.csv
```

### Générer les figures

```powershell
python -m pretest_campagne.scenario_a.plots.<figure_module> `
    --input results/mne3sd/scenario_a/<scenario_name>.csv `
    --figures-dir figures/mne3sd/scenario_a/ `
    --format pdf
```

### Lanceur de batch

```powershell
python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_a
```
