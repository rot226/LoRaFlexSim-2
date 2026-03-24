# `loraflexsim/`

This folder contains the active core of LoRaFlexSim-2.

## What you will find here

- the simulation engine;
- the dashboard (`loraflexsim/launcher/dashboard.py`);
- scenario and validation modules;
- the Python entrypoint `python -m loraflexsim`.

## Public positioning

- **Primary path**: dashboard.
- **Official command-line workflow**: `loraflexsim`.
- **Fallback**: `python -m loraflexsim`.

## Historical note

Legacy surfaces (`mobilesfrdth`, `sfrd`, `src`, `final`) should no longer be treated as live interfaces.
