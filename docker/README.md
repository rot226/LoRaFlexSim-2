# `docker/` : runner CI local pour LoRaFlexSim

Le dossier `docker/` est **conservé**.

## Décision retenue

`docker/` n'est **pas** l'environnement d'installation/de développement recommandé pour les utilisateurs du projet.

Le parcours officiel reste l'installation locale documentée dans le `README.md` racine, en priorité sous **Windows 11** avec **Python 3.11**.

Le rôle de `docker/` est plus précis : il sert de **runner CI local** pour exécuter rapidement les validations automatiques du dépôt dans un environnement Python isolé et jetable.

En pratique, ce dossier est utile pour :

- vérifier que le projet s'installe correctement depuis `pyproject.toml` ;
- lancer la suite de tests sans polluer l'environnement local ;
- reproduire un contrôle proche d'un job CI minimal ;
- fournir un point d'entrée conteneurisé aux contributeurs qui ne veulent pas installer toutes les dépendances à la main.

## Ce que fait exactement `docker/Dockerfile`

L'image :

1. part de `python:3.11-slim`, compatible avec `pyproject.toml` (`requires-python = ">=3.11,<3.13"`) ;
2. copie les fichiers nécessaires à l'installation du package et aux tests (`pyproject.toml`, `README.md`, `src/`, `tests/`, `requirements.txt`) ;
3. exécute les commandes suivantes pendant le build :

```sh
python -m pip install --no-cache-dir --upgrade pip setuptools wheel
python -m pip install --no-cache-dir -e . --no-build-isolation pytest
```

4. définit la commande par défaut suivante au démarrage du conteneur :

```sh
pytest -q
```

## Usage recommandé sous Windows 11

Les exemples ci-dessous sont écrits pour **PowerShell** depuis la **racine du dépôt**.

### 1. Construire l'image

```powershell
docker build -f docker/Dockerfile -t loraflexsim-local-ci .
```

### 2. Lancer le contrôle par défaut

Cette commande exécute exactement le `CMD` du `Dockerfile`, donc : `pytest -q`.

```powershell
docker run --rm loraflexsim-local-ci
```

## Commandes réellement exécutées et variantes utiles

### Commande par défaut du conteneur

```powershell
docker run --rm loraflexsim-local-ci
```

Commande exécutée dans le conteneur :

```sh
pytest -q
```

### Exécuter un fichier de tests précis

```powershell
docker run --rm loraflexsim-local-ci pytest -q tests/test_mobilesfrdth_cli.py
```

Commande exécutée dans le conteneur :

```sh
pytest -q tests/test_mobilesfrdth_cli.py
```

### Exécuter un sous-ensemble de tests par motif

```powershell
docker run --rm loraflexsim-local-ci pytest -q -k mobility
```

Commande exécutée dans le conteneur :

```sh
pytest -q -k mobility
```

### Vérifier que la CLI packagée est bien installée

```powershell
docker run --rm loraflexsim-local-ci python -m mobilesfrdth --help
```

Commande exécutée dans le conteneur :

```sh
python -m mobilesfrdth --help
```

## Ce que `docker/` n'est pas

Pour éviter toute ambiguïté :

- ce n'est **pas** la voie d'installation officielle recommandée aux utilisateurs ;
- ce n'est **pas** un environnement de développement complet avec montage de volume, hot reload ou outillage IDE ;
- ce n'est **pas** une simple archive technique passive ;
- ce n'est **pas** le support principal du dashboard en usage quotidien.

Si votre objectif est d'utiliser ou développer LoRaFlexSim au quotidien sous Windows 11, suivez d'abord le `README.md` racine et créez un environnement virtuel local Python 3.11.
