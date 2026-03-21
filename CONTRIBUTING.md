# Contribuer à LoRaFlexSim

Merci de votre intérêt pour LoRaFlexSim. Ce dépôt vise un usage communautaire : contributions de documentation, correctifs, exemples et améliorations de workflows sont bienvenues.

## Avant de contribuer

- Lisez le `README.md` pour suivre le parcours standard recommandé.
- Sous Windows 11, utilisez de préférence **PowerShell** avec **Python 3.11**.
- Pour les workflows avancés, consultez `docs/advanced_workflows.md` avant d’ajouter un nouveau script ou une nouvelle procédure.

## Types de contributions attendues

- clarification ou enrichissement de la documentation ;
- correction de bugs ;
- amélioration du dashboard ou de la CLI standard ;
- ajout d’exemples reproductibles ou d’outils d’analyse ;
- amélioration de l’expérience communautaire et open-source du dépôt.

## Workflow recommandé

1. Créez une branche dédiée à votre changement.
2. Faites des modifications ciblées et documentées.
3. Exécutez les vérifications pertinentes depuis la racine du dépôt :

```bash
make validate
```

Si `make` n’est pas disponible sous Windows, utilisez Git Bash, WSL ou un environnement équivalent.

4. Décrivez clairement dans votre commit et dans votre pull request :
   - le problème traité ;
   - la solution proposée ;
   - les vérifications réalisées ;
   - les limites éventuelles.

## Style de contribution

- privilégiez des changements petits et relisibles ;
- gardez une séparation nette entre parcours standard et workflows avancés ;
- évitez de casser les chemins ou commandes déjà documentés dans le `README.md` ;
- documentez tout nouveau comportement utilisateur ou toute nouvelle dépendance.

## Signaler un problème

Si vous ne proposez pas de correctif immédiat, ouvrez une issue en précisant :

- le contexte d’exécution ;
- les étapes de reproduction ;
- le comportement observé ;
- le comportement attendu ;
- les journaux, captures ou fichiers utiles si disponibles.

## Respect de la communauté

Merci d’adopter une communication constructive, inclusive et respectueuse dans les issues, discussions et pull requests. Si le dépôt publie un `CODE_OF_CONDUCT.md`, il s’applique à l’ensemble des échanges du projet.
