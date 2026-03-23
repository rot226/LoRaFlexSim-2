# Carte de référence du dépôt

Ce document fixe la lecture documentaire du dépôt après la décision de surface publique.

## Décision structurante

La surface publique de LoRaFlexSim est désormais :

1. **dashboard** : `panel serve loraflexsim/launcher/dashboard.py --show`
2. **CLI officielle** : `loraflexsim ...`
3. **compatibilité** : `mobilesfrdth ...`
4. **moteur historique** : `python -m loraflexsim.run ...`

Conséquence : tout langage présentant `mobilesfrdth` comme « CLI officielle recommandée » doit être considéré comme obsolète.

## Catégories utilisées

- **produit principal** : à mettre en avant pour les utilisateurs et le développement courant ;
- **backend officiel** : implémentation technique derrière la surface publique ;
- **historique / spécialisé** : à conserver mais à ne plus promouvoir comme point d’entrée principal ;
- **recherche / archive** : campagnes, reproductions et artefacts scientifiques ;
- **outillage / packaging** : support d’installation, wrappers, CI et maintenance.

## Carte dossier par dossier

| Dossier | Catégorie | Statut | Rôle documentaire |
| --- | --- | --- | --- |
| `loraflexsim/` | produit principal | officiel | cœur historique du simulateur, dashboard et moteur |
| `src/mobilesfrdth/` | backend officiel | officiel mais non public | implémente aujourd’hui la CLI exposée publiquement sous le nom `loraflexsim` |
| `docs/` | produit principal | officiel | documentation utilisateur et technique |
| `scripts/` | outillage / packaging | officiel | bootstrap et wrappers, dont `scripts/loraflexsim.*` |
| `config/` | produit principal | officiel | configuration partagée |
| `docker/` | outillage / packaging | officiel | conteneurisation et CI locale |
| `tests/` | produit principal | officiel | validation automatique |
| `final/` | historique / spécialisé | non canonique | reproduction d’anciens pipelines |
| `pretest_campagne/` | recherche / archive | non canonique | scénarios de recherche, comparaisons et archives |
| `sfrd/` | historique / spécialisé | non canonique | pipeline avancé distinct du flux public |
| `qos_cli/` | historique / spécialisé | non canonique | interface experte |
| `results/`, `figures/`, `flora-master/` | recherche / archive | non canonique | artefacts et références |

## Sous-dossiers explicitement ambigus

| Dossier | Statut | Décision |
| --- | --- | --- |
| `loraflexsim/launcher/` | officiel | point d’entrée du dashboard |
| `loraflexsim/run.py` | historique | moteur CLI bas niveau, à ne pas présenter comme parcours grand public principal |
| `src/mobilesfrdth/` | backend officiel | à conserver tant que la commande publique `loraflexsim` s’appuie dessus |
| `mobile-sfrd_th/` | legacy | archive, pas point d’entrée officiel |
| `pretest_campagne/archive_or_mock/mobile-sfrd/` | archive | comparaison historique uniquement |

## Conséquence pratique pour la documentation

Le `README.md` et les guides utilisateur doivent désormais :

- montrer **comment installer** ;
- montrer **comment lancer le dashboard** ;
- montrer **comment lancer `loraflexsim`** ;
- reléguer `mobilesfrdth` au rang de compatibilité ;
- reléguer `python -m loraflexsim.run` au rang d’interface historique / technique.
