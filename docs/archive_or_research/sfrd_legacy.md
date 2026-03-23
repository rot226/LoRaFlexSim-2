# Archive documentaire — ancien pipeline `sfrd/`

L’ancien dossier `sfrd/` a été retiré de l’arbre exécutable du dépôt.

Cette note conserve uniquement le contexte documentaire utile :

- il s’agissait d’une CLI spécialisée pour certaines campagnes SFRD ;
- elle servait à des validations ciblées, des agrégations dédiées et des calibrations UCB ;
- elle ne faisait pas partie du parcours public recommandé.

## Remplacement actuel

Pour un usage courant, utilisez désormais :

- la CLI officielle `loraflexsim` pour les campagnes reproductibles ;
- `loraflexsim/` pour le moteur et le dashboard ;
- `pretest_campagne/` pour les reproductions et workflows de recherche encore conservés ;
- `docs/archive_or_research/` pour les autres traces historiques.

## Commandes historiques conservées comme mémoire

```powershell
python -m sfrd.cli.run_campaign --network-sizes 80 160 320 640 1280 --replications 5 --seeds-base 1 --snir OFF,ON --algos UCB ADR MixRA-H MixRA-Opt --warmup-s 0
python -m sfrd.cli.validate_outputs --output-root <ancien_output_root>
python -m sfrd.cli.plot_campaign --campaign-id <ancien_campaign_id>
```

Ces commandes ne doivent plus être présentées comme actives dans le dépôt courant.
