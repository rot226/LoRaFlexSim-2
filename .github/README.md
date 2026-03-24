# `.github/`

## À quoi sert ce dossier ?

Ce dossier centralise l'automatisation GitHub du dépôt, en particulier les workflows CI/CD exécutés par GitHub Actions.

## Quand l’utiliser ?

- Quand vous devez modifier un workflow d'intégration continue ou de validation automatique.
- Quand une exécution GitHub Actions échoue et que vous devez comprendre le pipeline associé.
- Quand vous ajoutez une vérification de dépôt déclenchée côté GitHub.

## Quand ne pas l’utiliser ?

- Ne l'utilisez pas pour lancer une simulation locale ou modifier la logique métier Python.
- Ne commencez pas ici pour découvrir le projet : lisez d'abord le `README.md` racine puis la documentation de `docs/`.

## Point d’entrée / fichiers à ouvrir d’abord

- `.github/workflows/loraflexsim-smoke.yml` : workflow smoke de la CLI publique `loraflexsim`.
- `README.md` racine : vue d'ensemble du dépôt avant de modifier l'automatisation.
