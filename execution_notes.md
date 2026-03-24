# Execution Log

This branch documents attempts to follow the requested sequence.

## Completed steps
- Creation of a local virtual environment (`python -m venv .venv`) followed by activation.
- Offline installation of `setuptools` from the system wheel to satisfy the PEP 517 backend (`/usr/share/python-wheels/setuptools-68.1.2-py3-none-any.whl`).

## Blocking points
- `pip install -e .` fails because network access is filtered (HTTP 403 proxy errors while downloading dependencies), and `bdist_wheel` is unavailable without the `wheel` package.
- Core dependencies (e.g., `numpy`) cannot be installed for the same reason, which blocks execution of `python -m loraflexsim.run` even in fast mode.
- The `data/` and `plots/` directories do not exist, and no new CSV or EPS outputs could be generated until prerequisites are installed.

## Required actions to complete the sequence
- Provide offline wheels for `wheel`, `numpy`, `pandas`, `scipy`, `matplotlib`, and additional dependencies listed in `pyproject.toml`, or temporarily lift network restrictions during installation.
- Re-run `pip install -e .` once these packages are available, then execute in order: runner in `--fast` mode and full mode, `prepare_ieee_figures.py` to generate `_ieee.csv`, and finally EPS figure-generation scripts with `ieee_plot_style.yaml`.

## Scientific framing

### Observations
- The dependency installation path is currently constrained by network filtering and missing wheel artifacts.
- The execution chain cannot proceed to simulation and figure generation while these prerequisites are unavailable.

### Hypothesis
- Providing offline wheels or temporarily enabling dependency downloads should restore reproducible end-to-end execution.

### Limitations
- No runtime metrics (PDR, SNR, SNIR, RSSI) were produced in this state, so no quantitative validation can be reported yet.
