# Inventaire des scripts d’entrée utilisateur

Ce document recense les **points d’entrée utilisateur conservés dans le dépôt** avec, pour chacun, le **shell cible**, les **plateformes supportées**, l’**équivalent sur les autres plateformes** et les **dépendances préalables**.

## Règles de lecture

- **Windows 11** : shell documentaire prioritaire = **PowerShell**.
- **Linux / macOS** : shell documentaire prioritaire = **bash** (ou `zsh` pour les commandes `python ...`).
- Tous les fichiers `*.py` sont des **entrées cross-platform** : l’équivalent Windows/Linux/macOS est généralement la **même commande Python**, exécutée dans le shell local.
- Quand il n’existe **pas** de wrapper natif utile sur une autre plateforme, ce document indique le **fallback explicite** au lieu d’imposer une conversion implicite.
- Version Python cible du dépôt : **3.11 ou 3.12**.

## Dépendances de base par famille

| Famille | Dépendances minimales documentées |
| --- | --- |
| CLI `mobilesfrdth` en mode dépôt/offline | `matplotlib`, `PyYAML` |
| Runtime complet du dépôt | `python -m pip install -e . --no-build-isolation` |
| Tracés / comparatifs | Runtime complet + `matplotlib` ; `pandas` si lecture/agrégation CSV avancée |
| Dashboard | Runtime complet + `panel`, `plotly`, `numpy`, `pandas` |
| Archive `mobile-sfrd` | `pip install -r pretest_campagne/archive_or_mock/mobile-sfrd/requirements.txt` |
| Reproduction `scenario_c` | Runtime complet ; au minimum `numpy`, `pandas`, `matplotlib`, et `Pillow` pour `make_all_plots.py` |
| Build FLoRa natif | Toolchain Unix avec `make` |

## 1. Entrées officielles conservées hors des dossiers demandés

| Entrée | Shell cible | Plateformes supportées | Équivalent autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `mobilesfrdth` (console script installé depuis `src/mobilesfrdth/`) | PowerShell sous Windows, bash/zsh ailleurs | Windows 11, Linux, macOS | Fallback dépôt : `python -m mobilesfrdth`, `scripts/mobilesfrdth.ps1`, `scripts/mobilesfrdth.sh` | Python 3.11/3.12 ; runtime complet recommandé |
| `python -m loraflexsim.run` | PowerShell / bash / zsh | Windows 11, Linux, macOS | C’est déjà la forme portable | Runtime complet du dépôt |
| `panel serve loraflexsim/launcher/dashboard.py --show` | PowerShell / bash / zsh | Windows 11, Linux, macOS (ouverture auto partielle selon OS) | Même commande sur toutes plateformes | Runtime complet + dépendances dashboard |
| `python -m scripts.mne3sd.run_all_campaign_outputs` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet du dépôt |

## 2. Dossier `scripts/`

### 2.1 Wrappers, bootstrap et pipelines documentés

| Script | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `scripts/bootstrap_windows.ps1` | PowerShell | Windows 11 | `scripts/bootstrap_unix.sh` sous Linux/macOS | `py` avec Python 3.11/3.12, `venv`, `pip`, `setuptools` |
| `scripts/bootstrap_unix.sh` | bash | Linux, macOS | `scripts/bootstrap_windows.ps1` sous Windows | `python3.11` ou `python3.12`, `venv`, `pip` |
| `scripts/mobilesfrdth.ps1` | PowerShell | Windows 11 | `scripts/mobilesfrdth.sh` ou `python -m mobilesfrdth` | Python 3.11/3.12 ; `matplotlib`, `PyYAML` en mode offline ; runtime complet recommandé |
| `scripts/mobilesfrdth.sh` | bash | Linux, macOS | `scripts/mobilesfrdth.ps1` ou `python -m mobilesfrdth` | Python 3.11/3.12 ; `matplotlib`, `PyYAML` en mode offline ; runtime complet recommandé |
| `scripts/windows/run_offline.ps1` | PowerShell | Windows 11 | `scripts/run_offline.sh` sous Linux/macOS | Python 3.11/3.12 ; `matplotlib`, `PyYAML` |
| `scripts/run_offline.sh` | bash | Linux, macOS | `scripts/windows/run_offline.ps1` sous Windows | Python 3.11/3.12 ; `matplotlib`, `PyYAML` |
| `scripts/run_campaign_profiles.ps1` | PowerShell | Windows 11 | `scripts/run_campaign_profiles.sh` sous Linux/macOS | Python 3.11/3.12 ; `matplotlib`, `PyYAML` ou runtime complet |
| `scripts/run_campaign_profiles.sh` | bash | Linux, macOS | `scripts/run_campaign_profiles.ps1` sous Windows | Python 3.11/3.12 ; `matplotlib`, `PyYAML` ou runtime complet |
| `scripts/run_grid.ps1` | PowerShell | Windows 11 | `scripts/run_grid.sh` sous Linux/macOS | Python 3.11/3.12 ; `matplotlib`, `PyYAML` ou runtime complet |
| `scripts/run_grid.sh` | bash | Linux, macOS | `scripts/run_grid.ps1` sous Windows | Python 3.11/3.12 ; `matplotlib`, `PyYAML` ou runtime complet |
| `scripts/run_step1_matrix_windows.ps1` | PowerShell | Windows 11 | Fallback portable : `python scripts/run_step1_matrix.py ...` dans n’importe quel shell | Venv local `.venv` ou `env` ; runtime complet |

### 2.2 Scripts Bash sans équivalent Windows dédié

| Script | Shell cible | Plateformes supportées | Fallback Windows explicite | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `scripts/run_all_fast.sh` | bash | Linux, macOS | Exécuter sous PowerShell les **trois** commandes `python -m loraflexsim.run ...` déjà visibles dans le script ; Git Bash/WSL possibles mais non prioritaires | Runtime complet du dépôt |
| `scripts/run_ci_pipeline.sh` | bash | Linux, macOS | Lancer séparément sous PowerShell : `pytest -q`, `python -m scripts.mne3sd.run_all_campaign_outputs --campaign both --profile ci`, les sweeps `scenario_a` / `scenario_b`, puis `python scripts/run_validation.py --output results/validation_matrix.csv` | Runtime complet, `pytest` |
| `scripts/build_flora_cpp.sh` | bash | Linux, macOS | Pas de wrapper Windows utile documenté ; utiliser **WSL** ou une machine Unix si vous avez réellement besoin du backend `flora_cpp` | `make`, toolchain C/C++, arborescence `flora-master/` |

### 2.3 Entrées Python directement lançables

Ces scripts s’exécutent dans **PowerShell**, **bash** ou **zsh** avec la même forme : `python <script>.py ...`.

| Groupe de scripts | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| Exécutions / campagnes : `scripts/run_battery_tracking.py`, `run_channels_sweep.py`, `run_interval_sweep.py`, `run_mobility_latency_energy.py`, `run_mobility_models.py`, `run_mobility_multichannel.py`, `run_noise_sweep.py`, `run_per_monte_carlo.py`, `run_qos_cluster_bench.py`, `run_qos_cluster_pipeline.py`, `run_qos_comparison.py`, `run_rssi_snr_regression.py`, `run_step1_baseline.py`, `run_step1_essai_graphe.py`, `run_step1_experiments.py`, `run_step1_matrix.py`, `run_step1_scenarios.py`, `run_step1_window_campaign.py`, `run_step2_scenarios.py`, `run_validation.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet du dépôt |
| Simulations ciblées : `scripts/simulate_mobility_random_waypoint.py`, `simulate_mobility_smooth.py`, `simulate_mobility_vs_static.py`, `simulate_range_impact.py`, `benchmark_energy_classes.py`, `profile_simulation.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet du dépôt |
| Génération / agrégation / comparaison : `scripts/aggregate_step1_results.py`, `adjust_non_orth_delta.py`, `calibrate_snir_trend.py`, `compare_flora_channel.py`, `compare_run_configs.py`, `generate_adr_alignment_report.py`, `generate_all_figures.py`, `generate_fake_csv_essai.py`, `long_range_margin.py`, `qos_cluster_plots.py`, `scripts/mne3sd/export_node_summaries.py`, `scripts/mne3sd/run_all_campaign_outputs.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet ; `pandas`/`matplotlib` pour les exports et figures |
| Figures / visualisations : `scripts/plot_battery_tracking.py`, `plot_channels_sweep.py`, `plot_der_density.py`, `plot_interval_sweep.py`, `plot_mobility_latency_energy.py`, `plot_mobility_models.py`, `plot_mobility_multichannel.py`, `plot_node_positions.py`, `plot_noise_sweep.py`, `plot_sf_vs_scenario.py`, `plot_step1_comparison.py`, `plot_step1_extended_qos.py`, `plot_step1_results.py`, `plot_step2_comparison.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet ; `matplotlib` requis |
| Contrôles / validation : `scripts/sanity_checks.py`, `validate_article_consistency.py`, `validate_article_metrics.py`, `validate_ieee_readiness.py`, `validate_long_range.py`, `validate_qos_against_reference.py`, `validate_snir_plots.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet ; `matplotlib`/`pandas` selon le script contrôlé |

## 3. Dossier `final/`

| Entrée | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `final/run_all.ps1` | PowerShell | Windows 11 | `final/run_all.sh` sous Linux/macOS | Runtime complet du dépôt |
| `final/run_all.sh` | bash | Linux, macOS | `final/run_all.ps1` sous Windows | Runtime complet du dépôt |
| `final/plot_all.ps1` | PowerShell | Windows 11 | `final/plot_all.sh` sous Linux/macOS | Runtime complet ; `matplotlib` |
| `final/plot_all.sh` | bash | Linux, macOS | `final/plot_all.ps1` sous Windows | Runtime complet ; `matplotlib` |
| `final/scenarios/run_qos_baselines.py`, `final/scenarios/run_snir.py`, `final/scenarios/run_ucb1.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet du dépôt |
| `final/plots/plot_der_vs_nodes.py`, `final/plots/plot_snir_distribution.py`, `final/plots/plot_throughput.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet ; `matplotlib`, `pandas`/CSV selon le script |

## 4. Dossier `sfrd/`

Toutes les entrées `sfrd` sont des **modules Python portables** : le shell cible est simplement le shell local qui lance `python -m ...`.

| Entrée | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `python -m sfrd.cli.run_campaign` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet du dépôt |
| `python -m sfrd.cli.plot_campaign` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; `matplotlib`, `pandas` |
| `python -m sfrd.cli.validate_outputs` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m sfrd.cli.calibrate_ucb` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m sfrd.cli.check_trends` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m sfrd.parse.aggregate`, `python -m sfrd.parse.parse_run` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |

## 5. Dossier `pretest_campagne/`

### 5.1 MNE3SD : scénarios A, B et D

| Entrée | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_a` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet du dépôt |
| `python -m pretest_campagne.scenario_a.scenarios.run_class_density_sweep`, `run_class_downlink_energy_profile`, `run_class_load_sweep`, `simulate_energy_classes`, `simulate_pdr_density`, `simulate_pdr_load` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m pretest_campagne.scenario_a.plots.plot_class_density_metrics`, `plot_class_downlink_energy`, `plot_class_load_results`, `plot_energy_duty_cycle`, `plot_pdr_density_metrics`, `plot_pdr_load_metrics` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; `matplotlib` |
| `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_b` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m pretest_campagne.scenario_b.scenarios.run_mobility_gateway_sweep`, `run_mobility_range_sweep`, `run_mobility_speed_sweep` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m pretest_campagne.scenario_b.plots.plot_mobility_gateway_metrics`, `plot_mobility_range_metrics`, `plot_mobility_speed_metrics` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; `matplotlib` |
| `python -m scripts.mne3sd.run_all_campaign_outputs --campaign scenario_d` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m pretest_campagne.scenario_d.scenarios.run_mobility_gateway_sweep`, `run_mobility_range_sweep`, `run_mobility_speed_sweep` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m pretest_campagne.scenario_d.plots.plot_mobility_gateway_metrics`, `plot_mobility_range_metrics`, `plot_mobility_speed_metrics` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; `matplotlib` |

### 5.2 Scénario C

| Entrée | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `python -m pretest_campagne.scenario_c.run_all` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; au minimum `numpy`, `pandas`, `matplotlib` |
| `python -m pretest_campagne.scenario_c.make_all_plots` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; `matplotlib`, `Pillow` |
| `python -m pretest_campagne.scenario_c.all_plot_compare`, `compare_with_snir`, `plot_cluster_der`, `qa_scientific_checks`, `quick_check`, `report_integrity`, `reproduce_author_results`, `validate_results`, `diagnose_import` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; `matplotlib`/`pandas` selon l’outil |
| `python -m pretest_campagne.scenario_c.step1.run_step1`, `python -m pretest_campagne.scenario_c.step2.run_step2` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet |
| `python -m pretest_campagne.scenario_c.tools.aggregate_step1`, `aggregate_step2`, `inspect_results`, `smoke_pipeline`, `verify_all` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Runtime complet ; `pandas`/CSV selon l’outil |
| Tracés `pretest_campagne/scenario_c/step1/plots/plot_S*.py` et `pretest_campagne/scenario_c/step2/plots/plot_*.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet ; `matplotlib` |

### 5.3 Archive `iwcmc_archive`

| Entrée | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `pretest_campagne/iwcmc_archive/snir_static/run_campaign.ps1` | PowerShell | Windows 11 | `pretest_campagne/iwcmc_archive/snir_static/run_campaign.sh` | Runtime complet ; `matplotlib` pour les figures |
| `pretest_campagne/iwcmc_archive/snir_static/run_campaign.sh` | bash | Linux, macOS | `pretest_campagne/iwcmc_archive/snir_static/run_campaign.ps1` | Runtime complet ; `matplotlib` |
| `pretest_campagne/iwcmc_archive/rl_static/run_campaign.ps1` | PowerShell | Windows 11 | `pretest_campagne/iwcmc_archive/rl_static/run_campaign.sh` | Runtime complet ; `matplotlib` |
| `pretest_campagne/iwcmc_archive/rl_static/run_campaign.sh` | bash | Linux, macOS | `pretest_campagne/iwcmc_archive/rl_static/run_campaign.ps1` | Runtime complet ; `matplotlib` |
| `pretest_campagne/iwcmc_archive/rl_mobile/run_campaign.ps1` | PowerShell | Windows 11 | `pretest_campagne/iwcmc_archive/rl_mobile/run_campaign.sh` | Runtime complet ; `matplotlib` |
| `pretest_campagne/iwcmc_archive/rl_mobile/run_campaign.sh` | bash | Linux, macOS | `pretest_campagne/iwcmc_archive/rl_mobile/run_campaign.ps1` | Runtime complet ; `matplotlib` |
| `pretest_campagne/iwcmc_archive/archive/archive_results.ps1` | PowerShell | Windows 11 | `pretest_campagne/iwcmc_archive/archive/archive_results.sh` | `tar` + sorties déjà générées |
| `pretest_campagne/iwcmc_archive/archive/archive_results.sh` | bash | Linux, macOS | `pretest_campagne/iwcmc_archive/archive/archive_results.ps1` | `tar` + sorties déjà générées |
| Scripts Python d’archive : `overlay_iwcmc_figures.py`, `snir_static/scenarios/S1.py` à `S8.py`, `snir_static/plots/plot_S1.py` à `plot_S8.py`, `rl_static/scenarios/run_ucb1_vs_qos.py`, `rl_static/plots/plot_rls_figures.py`, `rl_mobile/scenarios/run_rl_mobile.py`, `rl_mobile/plots/plot_rlm_figures.py` | Python via shell local | Windows 11, Linux, macOS | Même commande Python sur toutes plateformes | Runtime complet ; `matplotlib` |

### 5.4 Archive `mobile-sfrd`

| Entrée | Shell cible | Plateformes supportées | Équivalent sur les autres plateformes | Dépendances préalables |
| --- | --- | --- | --- | --- |
| `python pretest_campagne/archive_or_mock/mobile-sfrd/run_all.py` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | `pip install -r pretest_campagne/archive_or_mock/mobile-sfrd/requirements.txt` |
| `python pretest_campagne/archive_or_mock/mobile-sfrd/validate_checklist.py` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Même dépendances que `run_all.py` |
| `python pretest_campagne/archive_or_mock/mobile-sfrd/experiments/exp1_pdr_vs_speed.py` à `exp5_changepoint.py` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Dépendances locales `mobile-sfrd` |
| `python pretest_campagne/archive_or_mock/mobile-sfrd/plotting/plot_fig1.py` à `plot_fig5.py` | PowerShell / bash / zsh | Windows 11, Linux, macOS | Même commande sur toutes plateformes | Dépendances locales `mobile-sfrd` + `matplotlib` |

## 6. Fallbacks explicitement documentés pour Windows 11

- **Vous restez sur le flux standard** : utilisez `mobilesfrdth`, `scripts/mobilesfrdth.ps1` ou `python -m mobilesfrdth`.
- **Vous tombez sur un script `.sh` sans équivalent Windows** :
  - si le script n’est qu’un **orchestrateur Python**, relancez les **commandes Python explicites** indiquées dans ce document ;
  - si le script dépend d’un vrai environnement Unix (`make`, `tar`, `nproc`, etc.), préférez **WSL**.
- **Vous êtes dans `final/`, `sfrd/` ou `pretest_campagne/`** : la plupart des points d’entrée utiles sont déjà des **modules Python portables** ; il n’y a donc pas de perte fonctionnelle sous PowerShell.

## 7. Recommandation courte

- **Nouveau flux / usage standard** : `mobilesfrdth`.
- **Automatisation dépôt** : wrappers dans `scripts/`.
- **Reproduction historique** : `final/`, `pretest_campagne/scenario_c/`, `pretest_campagne/iwcmc_archive/`, `pretest_campagne/archive_or_mock/mobile-sfrd/`.
- **Pipeline spécialisé SFRD** : `python -m sfrd.cli.*`.
