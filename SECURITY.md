# Security Policy

Thank you for supporting responsible security practices for LoRaFlexSim.

## Reporting a vulnerability

If you identify a security vulnerability, please **do not** disclose it publicly in an open issue. Use **private reporting** to the repository maintainers and include:

- a clear description of the vulnerability;
- affected components;
- reproducible steps;
- an initial **impact assessment**;
- any proposed **mitigation** if available.

## What to avoid

Until a fix is available, avoid publishing:

- secrets, credentials, or tokens;
- a full exploit;
- operational details that enable immediate compromise.

## Scope

This policy primarily covers:

- source code in this repository;
- execution and analysis scripts;
- documentation that could lead to insecure configuration.

## Contribution security best practices

Before submitting a change:

- verify that examples do not contain secrets;
- document security assumptions explicitly;
- report any sensitive dependency or notable network behavior.

## Patch publication

When a fix is ready, maintainers may publish a summary of the vulnerability, its impact, and the fixed version, with a level of detail aligned with **coordinated disclosure**.
