# `.github/`

## Purpose of this folder

This folder centralizes the repository's GitHub automation, especially CI/CD workflows executed by GitHub Actions.

## When to use it

- When you need to edit a continuous integration workflow or an automated validation workflow.
- When a GitHub Actions run fails and you need to understand the related pipeline.
- When you are adding a repository check triggered on the GitHub side.

## When not to use it

- Do not use this folder to run a local simulation or modify Python business logic.
- Do not start here to discover the project: read the root `README.md` first, then `docs/`.

## First files to open

- `.github/workflows/loraflexsim-smoke.yml`: smoke workflow for the public `loraflexsim` CLI.
- Root `README.md`: repository overview before changing automation.
