# `flora-master/`

## Positionnement local dans ce dépôt

Le dossier `flora-master/` est une **copie externe de référence liée à FLoRa** conservée dans
LoRaFlexSim-2 pour la **comparaison scientifique**, la **reproduction méthodologique** et
l'**archivage**. Il ne constitue pas le point d'entrée principal du projet : pour utiliser ou
faire évoluer LoRaFlexSim-2, commencez plutôt par `README.md`, `loraflexsim/` et la
documentation sous `docs/`.

## Statut du dossier

- **Référence externe / archive** : ce contenu est gardé pour relier le dépôt à son contexte
  FLoRa, pas comme implémentation canonique du flux principal.
- **Support de comparaison scientifique** : il sert lorsque l'on doit confronter un scénario,
  un paramétrage radio ou une sortie LoRaFlexSim à un équivalent FLoRa.
- **Vendored / reference only** : sauf besoin explicite de reproduction, de correction
  documentaire ou d'alignement scientifique, ce dossier doit être considéré comme non prioritaire
  à modifier et non comme zone de développement fonctionnel courant.

## Quand l'utiliser

- Quand vous devez comparer LoRaFlexSim à FLoRa.
- Quand une documentation ou un script de validation mentionne explicitement des fichiers FLoRa.
- Quand vous travaillez sur une reproduction ou un alignement avec le comportement du framework amont.

## Quand ne pas l'utiliser comme point d'entrée

- Ne l'utilisez pas pour le flux standard `mobilesfrdth`.
- Ne commencez pas ici pour découvrir le dépôt ou modifier la CLI Python principale.
- N'y ajoutez pas de logique spécifique au projet sans raison claire de compatibilité ou de reproduction.

## Contexte FLoRa

FLoRa reste le cadre de référence scientifique auquel ce dossier renvoie : on y retrouve une base
OMNeT++/LoRaWAN utile pour inspecter des configurations, relire certains scénarios historiques et
comparer des hypothèses radio avec celles reprises dans LoRaFlexSim-2.

## Point d'entrée / fichiers à ouvrir d'abord

- `flora-master/README.md` : ce mini-guide.
- `flora-master/simulations/omnetpp.ini` : configuration de simulation FLoRa.
- `flora-master/src/` : sources FLoRa si vous devez inspecter l'implémentation.
- `docs/reproduction_flora.md` et `scripts/compare_flora_channel.py` : points de raccord avec le reste du dépôt.
