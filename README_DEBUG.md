# Debug / Sanity checks

> [!TIP]
> **À quoi sert ce dossier ?** Documenter les vérifications rapides de cohérence sur les résultats CSV, notamment autour de SNIR, PDR et distributions.
>
> **Quand l’utiliser ?** Après une campagne de simulation, avant l’analyse détaillée ou lorsqu’un résultat paraît suspect.
>
> **Commande minimale** `python scripts/sanity_checks.py`
>
> **Sorties produites** Messages `WARN`/`FAIL` en console pour signaler les incohérences détectées dans les résultats.

## 1. Objectif du dossier

Le script `scripts/sanity_checks.py` vérifie rapidement la cohérence des sorties CSV (SNIR ON/OFF, PDR, distributions), et signale les anomalies sous forme de **WARN** ou **FAIL**.

## 2. Prérequis

### Politique locale alignée avec le README principal

- **OS documenté en priorité : Windows 11**.
- **Shell documenté : PowerShell**.
- **Répertoire d’exécution : racine du dépôt**.
- **Version Python recommandée : 3.11**.
- **Support packaging : Python 3.11 à 3.12**.
- **Installation standard recommandée :** `python -m pip install -e . --no-build-isolation` après activation du venv.
- **`PYTHONPATH=src` n’est pas requis** pour ces vérifications en usage standard.
- **`cmd.exe` n’est pas la cible documentaire principale** ; utilisez PowerShell.

## 3. Scénario minimal

Depuis la **racine du dépôt** dans **PowerShell** :

```powershell
python scripts/sanity_checks.py
```

## 4. Commande de run

### Usage

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

## 5. Agrégation

Il n’y a pas d’agrégation dédiée : ce flux inspecte directement les CSV déjà produits dans `results/`.

## 6. Plots

Aucun plot n’est généré par ce script : la sortie est textuelle et destinée à la validation rapide.

## 7. Rapport

Aucun rapport dédié n’est produit : les informations sont affichées dans la console pour un diagnostic immédiat.

## 8. Figures détaillées et options avancées

### Comportement vérifié

- Compare SNIR **ON** vs **OFF** sur **PDR / throughput / collisions** (Δ > ε).
- Alerte si **PDR/DER > 0,999** pour un nombre de nœuds élevé.
- Vérifie une **variance non nulle** pour les distributions **SF/SNR/SNIR/collisions** (histogrammes JSON).
- Alerte si **Jain == 1.0** pour toutes les lignes.

### Notes Windows 11

- Utilisez `python` ou `py -3.11` selon votre configuration (`py -3.11 scripts/sanity_checks.py`).
- Les chemins Windows (`C:\...`) sont acceptés pour `results/` si besoin.
- Si vous êtes en mode offline/fallback, activez d’abord le venv et utilisez le script documenté dans `README.md` si nécessaire.
