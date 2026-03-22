# `docker/`

## En 30 secondes

| Rubrique | Réponse rapide |
| --- | --- |
| **À quoi sert ce dossier ?** | Fournir un runner Docker minimal pour rejouer localement une validation proche de la CI. |
| **Quand l’utiliser ?** | Quand vous voulez vérifier l’installation du projet, lancer les tests dans un environnement jetable ou reproduire rapidement un contrôle CI local. |
| **Quand ne pas l’utiliser ?** | Ne l’utilisez pas comme environnement principal de développement quotidien ni comme parcours recommandé pour découvrir le projet. |
| **Point d’entrée principal** | `docker/Dockerfile`, puis `docker build -f docker/Dockerfile -t loraflexsim-local-ci .` et `docker run --rm loraflexsim-local-ci`. |
| **Sorties produites** | Un conteneur Python 3.11 prêt à exécuter `pytest -q` et, selon la commande lancée, les logs de tests ou d’aide CLI. |
| **Documentation détaillée** | Le README racine positionne `docker/` comme support officiel secondaire ; les commandes détaillées sont regroupées ci-dessous. |

Le dossier `docker/` est **conservé**.

## Documentation détaillée

### Décision retenue

`docker/` n'est **pas** l'environnement d'installation/de développement recommandé pour les utilisateurs du projet.

Le parcours officiel reste l'installation locale documentée dans le `README.md` racine, en priorité sous **Windows 11** avec **Python 3.11**.

Le rôle de `docker/` est plus précis : il sert de **runner CI local** pour exécuter rapidement les validations automatiques du dépôt dans un environnement Python isolé et jetable.

### Ce que fait `docker/Dockerfile`

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

### Usage recommandé sous Windows 11

Les exemples ci-dessous sont écrits pour **PowerShell** depuis la **racine du dépôt**.

#### Construire l'image

```powershell
docker build -f docker/Dockerfile -t loraflexsim-local-ci .
```

#### Lancer le contrôle par défaut

```powershell
docker run --rm loraflexsim-local-ci
```

### Variantes utiles

#### Exécuter un fichier de tests précis

```powershell
docker run --rm loraflexsim-local-ci pytest -q tests/test_mobilesfrdth_cli.py
```

#### Exécuter un sous-ensemble de tests par motif

```powershell
docker run --rm loraflexsim-local-ci pytest -q -k mobility
```

#### Vérifier que la CLI packagée est bien installée

```powershell
docker run --rm loraflexsim-local-ci python -m mobilesfrdth --help
```

### Ce que `docker/` n'est pas

- ce n'est **pas** la voie d'installation officielle recommandée aux utilisateurs ;
- ce n'est **pas** un environnement de développement complet avec montage de volume, hot reload ou outillage IDE ;
- ce n'est **pas** une simple archive technique passive ;
- ce n'est **pas** le support principal du dashboard en usage quotidien.
