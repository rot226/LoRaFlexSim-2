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

## Language policy

Project default language is **English**. To keep the documentation and contributor experience consistent, all public, user-facing content must be written in English by default:

- documentation pages and updates (`README`, `docs/`, contribution guides);
- UI text labels, messages, and notifications;
- CLI help text and examples;
- pull request titles/descriptions and issue descriptions intended for public project history.

French (or any other language) must only appear when intentionally localized and clearly scoped as localization content.

## Review checklist

Before requesting review, verify:

- [ ] No French strings in user-facing docs/UI unless intentionally localized.
- [ ] README and docs updated in English for any feature change.

## Reporting an issue

If you are not submitting an immediate fix, open an issue and include:

- runtime context;
- reproduction steps;
- observed behavior;
- expected behavior;
- relevant logs, screenshots, or files when available.

## Official bug procedure

When opening or triaging a bug, use the dedicated labels below:

- `bug`
- `regression`
- `docs-bug`
- `platform-windows`
- `ci-failure`

Set one severity level:

- `S1` (blocking)
- `S2` (major)
- `S3` (minor)

Use a bug issue template containing, at minimum:

- environment (OS, Python version, shell, branch/commit);
- command executed;
- expected result;
- observed result;
- logs (or CI output / stack trace).

### Definition of Done (bug fix)

A bug fix is considered done only when all of the following are completed:

1. a minimal reproduction is documented;
2. the fix is implemented;
3. a non-regression test is added or updated;
4. documentation is updated if user-facing behavior is impacted.

## Community respect

Please keep communication constructive, inclusive, and respectful in issues, discussions, and pull requests. If the repository publishes a `CODE_OF_CONDUCT.md`, it applies to all project interactions.
