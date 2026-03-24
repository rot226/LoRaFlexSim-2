# `scripts/`

Ce dossier regroupe les scripts d’automatisation et de bootstrap.

## Scripts à connaître en priorité

- `scripts/bootstrap_windows.ps1` : préparation environnement Windows 11.
- `scripts/loraflexsim.ps1` : wrapper Windows pour la CLI publique.
- `scripts/loraflexsim.sh` : wrapper Linux/macOS.
- `scripts/windows/run_offline.ps1` : pipeline offline Windows.

## Positionnement

- Les scripts complètent la surface publique.
- La surface publique reste : dashboard + `loraflexsim`.
- Les références aux anciennes surfaces (`mobilesfrdth`, `sfrd`, `src`, `final`) sont historiques uniquement.
