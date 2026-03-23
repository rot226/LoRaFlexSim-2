# `flora-master/`

## À quoi sert ce dossier ?

Ce dossier embarque une copie du framework FLoRa utilisé comme référence, comparaison ou base de reproduction autour d'OMNeT++ et LoRaWAN.

## Quand l’utiliser ?

- Quand vous devez comparer LoRaFlexSim à FLoRa.
- Quand une documentation ou un script de validation mentionne explicitement des fichiers FLoRa.
- Quand vous travaillez sur une reproduction ou un alignement avec le comportement du framework amont.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas pour le flux standard `mobilesfrdth`.
- Ne commencez pas ici pour découvrir le dépôt ou modifier la CLI Python principale.
- N'y ajoutez pas de logique spécifique au projet sans raison claire de compatibilité ou de reproduction.

## Point d’entrée / fichiers à ouvrir d’abord

- `flora-master/README.md` : ce mini-guide.
- `flora-master/simulations/omnetpp.ini` : configuration de simulation FLoRa.
- `flora-master/src/` : sources FLoRa si vous devez inspecter l'implémentation.
- `docs/reproduction_flora.md` et `scripts/compare_flora_channel.py` : points de raccord avec le reste du dépôt.
