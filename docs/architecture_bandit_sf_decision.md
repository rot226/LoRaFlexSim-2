# Note d’architecture — décision bandit SF (UCB1)

## Décision et mise à jour : responsabilité de `simulator.py`

La décision bandit sur le **Spreading Factor (SF)** est portée par le moteur d’événements dans `loraflexsim/launcher/simulator.py`, et **pas** par `loraflexsim/launcher/qos.py`.

### Point d’ancrage 1 — sélection SF avant émission (`TX_START`)

Dans la branche `TX_START`, la sélection SF UCB1 est déclenchée quand la condition suivante est vraie :

- `not node.adr and learning_method == "ucb1"`

Le simulateur instancie/utilise alors `node.sf_selector` puis appelle la sélection avant l’émission.

### Point d’ancrage 2 — mise à jour après verdict livraison (`TX_END`)

Dans la branche `TX_END`, après calcul du verdict de livraison, le simulateur met à jour le bandit via :

- `node.sf_selector.update(...)`

Autrement dit, la boucle décision → feedback du bandit SF est centralisée dans `simulator.py` aux événements `TX_START` / `TX_END`.

## Rôle de `qos.py`

`loraflexsim/launcher/qos.py` ne prend pas la décision SF bandit. Son rôle pertinent ici est de fournir le contexte QoS, notamment via :

- `qos_cluster_id` affecté au nœud,

puis exploité côté simulateur comme contexte injecté dans le calcul de récompense.
