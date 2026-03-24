# Exponential Traffic Validation

This document reports the values obtained while testing the
`traffic.exponential.sample_interval` function in the LoRaFlexSim simulator.

Parameters used:
- `mean_interval` = 10 seconds
- `N` = 10,000 samples
- `seed` = 0

Empirical measurements:
- Mean: 10.002 s
- Coefficient of variation: 1.0017
- KS test p-value: 0.968

These results originate from a local execution of `pytest` tests.

## Scientific interpretation

### Observations
- The sample mean (10.002 s) is consistent with `mean_interval = 10` seconds.
- The coefficient of variation (1.0017) is consistent with an exponential process.
- The KS p-value (0.968) does not indicate a detectable distribution mismatch at standard significance levels.

### Hypothesis
- Under identical seed and simulator configuration, repeated runs should preserve these statistics within Monte Carlo variability.

### Limitations
- These values were obtained for one seed (`seed = 0`) and one sample size (`N = 10,000`); they do not quantify cross-seed variability.
