# Guide utilisateur — Dashboard (voie principale)

Le dashboard est la voie principale pour utiliser LoRaFlexSim-2.

## Lancement (Windows 11)

```powershell
panel serve loraflexsim/launcher/dashboard.py --show
```

## Premier essai recommandé

1. Lancer la commande ci-dessus.
2. Régler un petit scénario (ex. 10 nœuds, 1 passerelle).
3. Cliquer sur **Lancer la simulation**.
4. Lire les indicateurs (PDR, collisions, énergie, délai, débit).
5. Exporter les résultats si nécessaire. Voir la [documentation des exports CSV du dashboard](dashboard_export.md) pour comprendre les fichiers générés et les ouvrir sous Windows/Excel.

## Quand passer à la CLI ?

Passez à `loraflexsim` si vous devez enchaîner automatiquement `run -> aggregate -> plots -> validate`.

## Ce qui n’est plus une surface vivante

Les anciens espaces `mobilesfrdth`, `sfrd/`, `src/` et `final/` ne sont plus des points d’entrée à documenter pour les nouveaux utilisateurs.
