# Author curves

This directory is reserved for author-provided datasets (reference curves) to overlay with LoRaFlexSim results.

## Expected CSV format

The script `pretest_campagne/scenario_c/reproduce_author_results.py` looks by default for `author_curves.csv` in this directory. It must contain the following columns:

- `figure`: figure identifier (`4`, `5`, `7`, `8`).
- `profile`: QoS profile (`mixra`, `apra`, `aimi`).
- `cluster`: cluster name (`gold`, `silver`, `bronze`, `all`, etc.).
- `x`: numeric x-axis value (network size, load level, etc.).
- `y`: numeric y-axis value (DER, throughput, etc.).
- `label`: optional legend text.

## Minimal example

```
figure,profile,cluster,x,y,label
4,mixra,gold,50,0.12,Authors MixRA
```

Additional rows are optional. If the file is missing or empty, the script plots simulated results only.
