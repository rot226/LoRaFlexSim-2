# Carte de référence du dépôt

Ce document sert de **référence unique** pour statuer sur les dossiers structurants du dépôt. Il complète le `README.md` :

- le `README.md` expose une vue courte et immédiatement visible ;
- ce document fixe la **catégorie**, le **statut** et l'**action cible** de chaque dossier top-level ;
- les décisions ci-dessous sont des **décisions de gouvernance documentaire** : elles clarifient la cible d'organisation ; pour `mobilesfrdth`, la convergence vers `src/mobilesfrdth/` est désormais matérialisée dans l'arbre du dépôt.

## Catégories utilisées

- **produit principal / flux standard** : chemins à privilégier pour un usage communauté ou pour le développement courant.
- **compatibilité / legacy** : composants historiques, spécialisés ou maintenus pour compatibilité.
- **recherche / archive** : campagnes de reproduction, artefacts scientifiques, jeux de résultats ou archives.
- **outillage / packaging** : scripts, métadonnées, exemples et aides de packaging.
- **conteneur / CI** : automatisation de build, intégration continue et conteneurisation.

## Décisions dossier par dossier

| Dossier | Catégorie | Statut explicite | Action unique | Description visible / justification |
| --- | --- | --- | --- | --- |
| `.github/` | conteneur / CI | Support d'automatisation du dépôt. | conserver tel quel comme point d’entrée officiel | Centralise les workflows GitHub et la plomberie CI autour du dépôt. |
| `config/` | produit principal / flux standard | Configuration partagée du simulateur. | conserver tel quel comme point d’entrée officiel | Porte les paramètres communs utilisés par le flux standard. |
| `docker/` | conteneur / CI | Référence unique pour l'image conteneur. | conserver tel quel comme point d’entrée officiel | **Décision explicite** : `docker/` reste le point d'entrée officiel pour la conteneurisation et la CI locale. |
| `docs/` | produit principal / flux standard | Documentation fonctionnelle et technique active. | conserver tel quel comme point d’entrée officiel | Rassemble les guides utilisateur, la validation et la gouvernance documentaire. |
| `examples/` | outillage / packaging | Exemples d'exécution et scripts de démonstration. | conserver tel quel comme point d’entrée officiel | Sert de zone d'exemples reproductibles pour l'adoption du projet. |
| `experiments/` | recherche / archive | Configurations de campagnes exploratoires. | déplacer sous `pretest_campagne/` | Les presets d'expériences avancées doivent converger avec les autres campagnes de recherche sous `pretest_campagne/`. |
| `figures/` | recherche / archive | Réceptacle de figures générées et comparatifs. | convertir en simple archive/documentation | Les figures versionnées sont utiles comme référence, mais ne doivent pas être présentées comme point d'entrée fonctionnel. |
| `final/` | compatibilité / legacy | Pipeline historique de CSV/figures, encore documenté pour reproduction. | convertir en simple archive/documentation | **Décision explicite** : `final/` n'est plus la voie recommandée pour l'usage standard ; il reste un flux historique de reproduction. |
| `flora-master/` | recherche / archive | Copie de référence externe liée aux travaux FLoRa. | convertir en simple archive/documentation | Dossier conservé pour traçabilité scientifique et comparaison, pas comme point d'entrée courant. |
| `loraflexsim/` | produit principal / flux standard | Cœur applicatif du dashboard et du simulateur. | conserver tel quel comme point d’entrée officiel | C'est l'un des deux socles techniques à privilégier pour le produit principal. |
| `mobile-sfrd/` | recherche / archive | Générateur expérimental « mock » séparé du simulateur principal. | convertir en simple archive/documentation | **Décision explicite** : `mobile-sfrd/` est conservé comme archive expérimentale documentée, sans rôle d'entrée officielle. |
| `mobile-sfrd_th/` | compatibilité / legacy | Archive legacy documentée ; le doublon `src/mobilesfrdth/` interne a été retiré. | convertir en simple archive/documentation | **Décision explicite** : le code packagé `mobilesfrdth` vit uniquement sous `src/mobilesfrdth/`; `mobile-sfrd_th/` reste une archive de contexte. |
| `numpy_stub/` | compatibilité / legacy | Compatibilité locale / stub minimal de dépendance. | conserver tel quel comme point d’entrée officiel | Utilitaire de compatibilité conservé tant qu'il répond à un besoin d'exécution/tests hors dépendances complètes. |
| `plots/` | outillage / packaging | Scripts de tracé transverses hors pipeline principal. | conserver tel quel comme point d’entrée officiel | Zone d'outillage pour les graphes transverses et diagnostics. |
| `pretest_campagne/` | recherche / archive | Racine canonique des campagnes de recherche et reproductions. | conserver tel quel comme point d’entrée officiel | Point d'ancrage officiel pour les scénarios historiques, migrations et reproductions scientifiques. |
| `qos_cli/` | compatibilité / legacy | CLI spécialisée distincte du parcours communauté. | convertir en simple archive/documentation | Son rôle devient documentaire/avancé tant qu'aucune convergence produit n'est décidée. |
| `results/` | recherche / archive | Résultats versionnés, rapports et sorties consolidées. | convertir en simple archive/documentation | Les résultats existants sont conservés comme référence ; la documentation doit primer sur l'usage direct du dossier. |
| `scipy/` | compatibilité / legacy | Compatibilité locale / stub léger autour de SciPy. | conserver tel quel comme point d’entrée officiel | Conservé comme support technique tant que l'environnement du dépôt en dépend. |
| `scripts/` | outillage / packaging | Scripts d'automatisation, bootstrap, validation et conversion. | conserver tel quel comme point d’entrée officiel | Dossier de référence pour l'automatisation locale et les tâches de maintenance. |
| `sfrd/` | compatibilité / legacy | CLI SFRD spécialisée, séparée du flux standard `mobilesfrdth`. | convertir en simple archive/documentation | **Décision explicite** : `sfrd/` reste documenté pour campagnes avancées/historiques, mais n'est plus une entrée standard. |
| `src/` | produit principal / flux standard | Racine du code packagé installé par `pip install -e .`. | conserver tel quel comme point d’entrée officiel | C'est la racine officielle du code Python packagé. |
| `tests/` | produit principal / flux standard | Référentiel de validation automatique. | conserver tel quel comme point d’entrée officiel | La qualité du produit repose sur cette base de tests. |
| `traffic/` | produit principal / flux standard | Composants trafic/utilitaires liés au comportement réseau. | conserver tel quel comme point d’entrée officiel | Contribue au flux standard de simulation et aux scénarios réseau. |

## Sous-dossier critique explicitement demandé

Même s'il n'est pas top-level, le dossier ci-dessous doit être statué explicitement car il fait partie des points d'ambiguïté du dépôt.

| Dossier | Catégorie | Statut explicite | Action unique | Description visible / justification |
| --- | --- | --- | --- | --- |
| `src/mobilesfrdth/` | produit principal / flux standard | Implémentation canonique de la CLI `mobilesfrdth`. | conserver tel quel comme point d’entrée officiel | **Décision explicite** : `src/mobilesfrdth/` est la source officielle à conserver ; toute duplication depuis `mobile-sfrd_th/` doit être résorbée ici. |

## Décisions structurantes à retenir

1. **Entrées officielles à privilégier** : `loraflexsim/`, `src/`, `src/mobilesfrdth/`, `docs/`, `config/`, `scripts/`, `docker/`.
2. **Zone officielle de recherche / reproduction** : `pretest_campagne/`, avec convergence souhaitée des contenus exploratoires de `experiments/`.
3. **Éléments à traiter comme historiques ou non prioritaires** : `mobile-sfrd/`, `sfrd/`, `final/`, `qos_cli/`, `flora-master/`, `figures/`, `results/`.
4. **Chevauchement résorbé pour le package** : le seul code source canonique de `mobilesfrdth` est `src/mobilesfrdth/`; `mobile-sfrd_th/` ne contient plus de package Python actif.

## Conséquence documentaire

Le `README.md` doit toujours refléter au minimum :

- la catégorie du dossier ;
- son statut lisible ;
- l'action cible décidée ;
- et, pour les cas ambigus, le dossier de référence vers lequel l'équipe doit converger.
