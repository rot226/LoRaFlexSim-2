# Language migration status and style guide

## Target register

All technical documentation must use **scientific/technical English**:

- precise, testable, and reproducible wording;
- explicit assumptions, units, and variable names;
- neutral tone (no marketing or colloquial style);
- stable terminology across modules, CLI guides, and validation notes.

## Terminology rules

Use the following canonical terms consistently:

- **node** (not "end-device" unless protocol-specific detail is required);
- **gateway** (for LoRaWAN gateway entities);
- **uplink / downlink** (directional radio traffic);
- **propagation** (radio/channel propagation models and conditions);
- **validation** (for checks against requirements, baselines, or references).

Recommended patterns:

- "node density", "gateway density", "uplink success rate", "downlink latency";
- "propagation model", "path-loss model", "fading profile";
- "validation profile", "validation matrix", "validation baseline".

## Language-mixing policy

- FR/EN mixing is **forbidden** in standard technical documentation.
- French is allowed only in explicitly localized content (e.g., `*.fr.md` or a clearly marked localization section).
- Code blocks, command examples, and protocol literals must stay unchanged unless a functional correction is required.

## Operational checklist for maintainers

1. Scan edited Markdown files for non-English prose before merge.
2. Keep headings, captions, and callouts in English.
3. If localized content is added intentionally, mark it explicitly and isolate it from canonical docs.
