# Guide utilisateur — dashboard

Ce guide présente le chemin le plus simple pour un premier usage de LoRaFlexSim via l’interface graphique Panel.

## Lancement

Depuis la racine du dépôt :

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

Si le navigateur ne s’ouvre pas automatiquement, récupérez l’URL affichée dans le terminal puis ouvrez-la manuellement.

## Réglages minimaux pour un premier test

Pour un premier essai, gardez les valeurs par défaut et modifiez seulement :

- **Nombre de nœuds**
- **Nombre de passerelles**
- **Mode d’émission**
- **Intervalle moyen (s)**
- **Nombre de paquets par nœud**
- **Graine** pour reproduire le test

Les paramètres avancés (mobilité, QoS, SNIR, batterie, positions manuelles, heatmap, réglages FLoRa) peuvent être laissés inchangés au début.

## Premier essai recommandé

1. Lancez `panel serve loraflexsim/launcher/dashboard.py --show`.
2. Réglez par exemple **Nombre de nœuds = 10** et **Nombre de passerelles = 1**.
3. Choisissez **Mode d’émission = Aléatoire**.
4. Fixez **Nombre de paquets par nœud = 20**.
5. Cliquez sur **Lancer la simulation**.
6. Consultez les indicateurs visibles : PDR, collisions, énergie, délai, débit.
7. Utilisez **Exporter résultats** si vous souhaitez conserver une sortie.

## Quand utiliser le dashboard ?

Le dashboard est adapté si vous voulez :

- découvrir rapidement le simulateur ;
- démontrer un scénario de façon visuelle ;
- tester des paramètres sans écrire une commande complète ;
- obtenir une première intuition avant de passer à une campagne CLI.

## Limites du dashboard

Le dashboard est moins pratique pour :

- exécuter beaucoup de variantes ;
- archiver systématiquement des campagnes ;
- automatiser un pipeline complet de simulation, agrégation, figures et validation.

Dans ces cas, utilisez plutôt `docs/user_guide_cli.md`.
