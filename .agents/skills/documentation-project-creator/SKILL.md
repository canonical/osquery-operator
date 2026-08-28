---
name: documentation-project-creator
description: >
  Orchestrates the setup of a Read the Docs documentation project in a GitHub repository based
  on the Canonical Sphinx Stack. Routes work through three sequential phases: project setup,
  structure building, and finalization.
  WHEN: set up RTD project, RTD project setup
license: Apache-2.0
metadata:
  author: Canonical/platform-engineering
  summary: Sets up RTD project according to Canonical Sphinx Stack, updates index pages, broken links, and fixes build warnings and failures.
  version: "2.0.0"
  tags:
    - canonical
    - rtd
    - setup
    - sphinx-stack
---

# documentation-project-creator

## Description

This skill sets up a Read the Docs (RTD) documentation project in a GitHub repository based on the [Canonical Sphinx Stack](https://github.com/canonical/sphinx-stack) (formerly `sphinx-docs-starter-pack`, now Sphinx Stack 2.0). It copies the required Sphinx and RTD files into the target repository, configures them for the specific project, and prepares the documentation structure following the Diátaxis approach.

> **Note:** This skill uses a copy-based setup: it copies files from the upstream Sphinx Stack into the target repository. Sphinx Stack 2.0 also ships a self-update flow (`make update`, backed by `docs/_dev/update_sp.py`), but this skill does **not** use it — new-project setup is always done by copying files as described in Phase 1.

The work is split into three sequential phases. Execute each phase in order using `read_file` to load the sub-skill instructions.

## Assumptions

- The upstream source is [`canonical/sphinx-stack`](https://github.com/canonical/sphinx-stack) (Sphinx Stack 2.0). In 2.0 the development tooling directory is `docs/_dev/` (previously `docs/.sphinx/`) and there is no longer a `docs/reuse/` directory.
- Documentation already lives in `docs/` in the target repository.
- The repository contains `charmcraft.yaml` and/or `metadata.yaml` (at root or in immediate subdirectories for mono-repos).
- You are working on a branch other than `main`.
- The user will be prompted for `newDomain` (canonical URL, no `https://`, no trailing `/`).
- GitHub token must have `workflow` scope — verify with `gh auth status` before starting.

---

## Execution order

| Phase | Sub-skill file | Scope |
|---|---|---|
| 1 | [`documentation-project-setup.md`](references/documentation-project-setup.md) | Clone Sphinx Stack, copy files, configure `conf.py`, pin dependencies (Steps 1–7) |
| 2 | [`documentation-structure-builder.md`](references/documentation-structure-builder.md) | Index pages, landing pages, URL-rewrite script, anchors, links, MyST conversion (Steps 8–16) |
| 3 | [`documentation-finalizer.md`](references/documentation-finalizer.md) | Contribute page, Juju intersphinx, README, repo files, QA loop (Steps 17–21) |

### Hand-off between phases

Phase 1 establishes shared state that later phases depend on:
- **Charm name** — from `charmcraft.yaml` / `metadata.yaml`
- **GitHub URL** — from `links.source` or `source`
- **Human-readable project name** — confirmed with user in Phase 1 Step 5
- **`newDomain` value** — prompted from user at skill start

Carry these values forward into Phases 2 and 3.

---

## Reference files

| File | Purpose |
|---|---|
| [`contribute-template.rst`](assets/contribute-template.rst) | RST template for the "How to contribute" page (used in Phase 3 Step 1) |
| [`juju-intersphinx-targets.md`](assets/juju-intersphinx-targets.md) | Lookup table for Juju intersphinx anchor targets (used in Phase 3 Step 2) |
| [`PR-GUIDE.md`](assets/PR-GUIDE.md) | PR description structure, reviewer priority tiers, and human action items |

---

## After all phases complete

Read [`PR-GUIDE.md`](assets/PR-GUIDE.md) and use it to structure the PR description, including:
- The `## For reviewers` section with high/medium/low priority file tiers
- The `## Items requiring human action` checklist
 - Archive and lock old Discourse pages once the RTD migration is verified.