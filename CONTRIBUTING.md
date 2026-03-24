# Contributing to LoRaFlexSim

Thank you for your interest in LoRaFlexSim. This repository is intended for community use: documentation contributions, bug fixes, examples, and workflow improvements are welcome.

## Before contributing

- Read `README.md` to follow the recommended standard path.
- On Windows 11, prefer **PowerShell** with **Python 3.11**.
- For advanced workflows, read `docs/advanced_workflows.md` before adding a new script or procedure.

## Expected contribution types

- documentation clarification or enrichment;
- bug fixes;
- dashboard or standard CLI improvements;
- reproducible examples or analysis tools;
- improvements to the repository's community and open-source experience.

## Recommended workflow

1. Create a branch dedicated to your change.
2. Make focused, documented modifications.
3. Run relevant checks from the repository root:

```bash
make validate
```

If `make` is not available on Windows, use Git Bash, WSL, or an equivalent environment.

4. Clearly describe in your commit and pull request:
   - the problem addressed;
   - the proposed solution;
   - the checks performed;
   - any known limitations.

## Contribution style

- prefer small, reviewable changes;
- keep a clear separation between the standard path and advanced workflows;
- avoid breaking paths or commands already documented in `README.md`;
- document any new user-visible behavior or dependency.

## Reporting an issue

If you are not submitting an immediate fix, open an issue and include:

- runtime context;
- reproduction steps;
- observed behavior;
- expected behavior;
- relevant logs, screenshots, or files when available.

## Community respect

Please keep communication constructive, inclusive, and respectful in issues, discussions, and pull requests. If the repository publishes a `CODE_OF_CONDUCT.md`, it applies to all project interactions.
