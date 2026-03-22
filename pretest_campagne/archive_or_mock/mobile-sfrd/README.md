# mobile-sfrd

> [!WARNING]
> **Statut : archive d’un mock pédagogique historique.**
>
> **Ce que c’est :** un mini-générateur déterministe et simplifié qui produit cinq jeux de résultats/figures LoRa mobiles à visée pédagogique ou de démonstration.
>
> **Quand l’utiliser :** pour illustrer rapidement un mock léger, rejouer un exemple historique très simplifié, ou comparer un artefact d’enseignement avec le flux officiel.
>
> **Quand ne pas l’utiliser :** pour un premier usage du dépôt, une campagne standard, une validation produit, une étude PHY complète ou toute exécution que la documentation présente comme supportée.
>
> **Point d’entrée officiel à utiliser à la place :** `mobilesfrdth` depuis la racine du dépôt.

## Décision de statut

`mobile-sfrd` n’est pas un outil encore supporté. Le dossier est conservé comme **archive d’un mock pédagogique historique** sous `pretest_campagne/archive_or_mock/` afin d’éviter toute confusion avec le flux standard.

> Ce projet **n'est pas** un simulateur PHY complet et ne vise pas à reproduire fidèlement toute la pile radio.

## Prérequis et installation

- Python 3.10+
- Environnement virtuel recommandé

Installation des dépendances :

```bash
pip install -r requirements.txt
```

## Exécution unique

Depuis le dossier `pretest_campagne/archive_or_mock/mobile-sfrd/`, lancez :

```bash
python run_all.py
```

Cette commande exécute les 5 expériences dans l'ordre et génère les sorties dans `outputs/csv/` et `outputs/figures/`.

## Sorties attendues

Après exécution, vous devez retrouver :

- CSV : `fig1.csv`, `fig2.csv`, `fig3.csv`, `fig4.csv`, `fig5.csv`
- Figures : `figure1.png`, `figure2.png`, `figure3.png`, `figure4.png`, `figure5.png`

## Personnalisation

Les paramètres peuvent être ajustés via les fichiers YAML de `config/` (`fig1.yaml` à `fig5.yaml`) :

- `N` (taille de réseau / nombre de nœuds)
- `seed` / seeds (contrôle de l'aléatoire)
- `changepoint_t` (instant de changement pour les scénarios à rupture)
- vitesses (`speeds`)
- style des figures (palette, taille, grille, etc.)

## Reproductibilité et dépendances externes

- Le pipeline est **déterministe** lorsque les seeds sont fixées.
- Le projet fonctionne sans dépendance OMNeT++/FLoRa.

## Alternative officielle

Pour un workflow standard maintenu, utilisez plutôt :

```powershell
mobilesfrdth --help
mobilesfrdth presets --list
```

Consultez `docs/user_guide_cli.md` pour le flux standard complet.

## Validation checklist (automatique)

Après `python run_all.py`, vous pouvez valider les contraintes du cahier des charges avec :

```bash
python validate_checklist.py
```

Ce script vérifie notamment :
- colonnes exactes des CSV attendus ;
- monotonie PDR/DER selon la vitesse et contrainte `RWP < SM` ;
- ordre d'apprentissage `v=1 > v=5 > v=10` (convergence + plateau) ;
- somme des barres Figure 3 = 200 par panneau/fenêtre ;
- rupture nette à `t=150` puis récupération partielle pour la Figure 5.
