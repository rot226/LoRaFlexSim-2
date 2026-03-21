# Debug / Sanity checks

## Politique locale alignée avec le README principal

- **OS documenté en priorité : Windows 11**.
- **Shell documenté : PowerShell**.
- **Répertoire d’exécution : racine du dépôt**.
- **Version Python recommandée : 3.11**.
- **Support packaging : Python 3.11 à 3.12**.
- **Installation standard recommandée :** `python -m pip install -e . --no-build-isolation` après activation du venv.
- **`PYTHONPATH=src` n’est pas requis** pour ces vérifications en usage standard.
- **`cmd.exe` n’est pas la cible documentaire principale** ; utilisez PowerShell.

## Sanity checks SNIR/PDR

Le script `scripts/sanity_checks.py` vérifie rapidement la cohérence des sorties CSV (SNIR ON/OFF, PDR, distributions), et signale les anomalies sous forme de **WARN** ou **FAIL**.

## Usage

Depuis la **racine du dépôt** dans **PowerShell** :

```powershell
# Analyse par défaut (tous les CSV sous results/)
python scripts/sanity_checks.py

# Cibler un dossier de résultats spécifique
python scripts/sanity_checks.py results/step1

# Ajuster les seuils
python scripts/sanity_checks.py results/step1 --epsilon 0.02 --large-nodes 150 --pdr-der-threshold 0.999

# Échouer si un WARN est détecté
python scripts/sanity_checks.py results/step1 --fail-on-warn
```

## Comportement vérifié

- Compare SNIR **ON** vs **OFF** sur **PDR / throughput / collisions** (Δ > ε).
- Alerte si **PDR/DER > 0,999** pour un nombre de nœuds élevé.
- Vérifie une **variance non nulle** pour les distributions **SF/SNR/SNIR/collisions** (histogrammes JSON).
- Alerte si **Jain == 1.0** pour toutes les lignes.

## Notes Windows 11

- Utilisez `python` ou `py -3.11` selon votre configuration (`py -3.11 scripts/sanity_checks.py`).
- Les chemins Windows (`C:\...`) sont acceptés pour `results/` si besoin.
- Si vous êtes en mode offline/fallback, activez d’abord le venv et utilisez le script documenté dans `README.md` si nécessaire.
