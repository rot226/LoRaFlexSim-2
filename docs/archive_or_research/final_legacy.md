# Archive documentaire — ancien pipeline `final/`

L’ancien dossier `final/` a été retiré de l’arbre exécutable du dépôt.

Cette note conserve uniquement le contexte documentaire utile :

- il s’agissait d’un pipeline historique simple centré sur l’export CSV et la génération de figures ;
- il servait à rejouer des sorties héritées alignées avec d’anciens documents ;
- il ne constitue plus le flux recommandé pour un usage moderne.

## Remplacement actuel

Pour un usage courant, utilisez désormais :

- `loraflexsim` comme point d’entrée officiel ;
- `loraflexsim/` pour le moteur historique et le dashboard ;
- `pretest_campagne/` pour les reproductions de recherche toujours maintenues ;
- `docs/archive_or_research/` pour la mémoire documentaire des anciens exports.

## Commandes historiques conservées comme mémoire

```powershell
python -m loraflexsim.run --nodes 30 --gateways 1 --mode random --interval 10 --steps 100 --output <ancien_csv>
python examples/analyse_resultats.py <ancien_csv> --output-dir <ancien_dossier_figures> --basename pdr_by_nodes
```

Ces commandes restent décrites uniquement pour comprendre l’ancien pipeline documentaire.
