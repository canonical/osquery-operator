---
name: documentation-project-setup
description: "Phase 1 of the documentation-project-creator skill. Sets up the Sphinx/RTD environment: clones the Sphinx Stack, copies core files, configures conf.py, and pins dependencies."
---

# documentation-project-setup

**Prerequisites:** This is Phase 1 of the `documentation-project-creator` skill. See the parent [SKILL.md](SKILL.md) for assumptions and the full workflow overview.

---

## Instructions

### Step 1 (global Step 1): Clone the Sphinx Stack and copy core files

Clone the [Sphinx Stack](https://github.com/canonical/sphinx-stack) (`canonical/sphinx-stack`, formerly `sphinx-docs-starter-pack`) into a temporary directory, then copy the following files into the target repository:

**At the repository root:**
- `.readthedocs.yaml`
- `.github/workflows/cla-check.yml` (if the repository doesn't already have a CLA check)

**In `docs/`:**
- `docs/.gitignore`
- `docs/Makefile`
- `docs/conf.py`
- `docs/requirements.txt`
- `docs/redirects.txt`
- All files in `docs/_dev/` (create this directory). This is the development tooling directory (renamed from `docs/.sphinx/` in Sphinx Stack 2.0). It contains `.pymarkdown.json` (required for `make lint-md`), `get_vale_conf.py`, `pa11y.json`, `update_sp.py`, `version`, and `.pre-commit-config.yaml`.
- All files in `docs/_templates/` (create this directory). Contains `header.html` and `footer.html` (used by the cookie banner in Phase 2).

> **Note:** Sphinx Stack 2.0 no longer ships a `docs/reuse/` or `docs/.sphinx/` directory — do not create or copy either. The Vale configuration is now generated automatically into `docs/_dev/` at build time (there is no committed `.vale.ini`).

**Files that ship with the Sphinx Stack but must be merged rather than overwritten:** `docs/.custom_wordlist.txt` and `docs/redirects.txt` may already exist in the target repository. If they do, merge the upstream content into the existing file instead of overwriting it. `docs/redirects.txt` must exist because the Sphinx Stack configures `sphinx-rerediraffe` with `rediraffe_redirects = "redirects.txt"` in `conf.py`, and `make html` will fail if this file is missing.

> **Note:** The Sphinx Stack also ships a `docs/index.rst` and Diátaxis content directories (`tutorials/`, `how-to/`, `reference/`, `explanation/`, `contribute/`) as example content. **Do not** copy these into the target repository — the target already has its own `docs/` content, which Phase 2 restructures.

### Step 2 (global Step 2): Set up GitHub Actions workflows

Check whether `.github/workflows/docs_rtd.yaml` exists. If it does not, create it with the following content, which calls the consolidated RTD workflow from `operator-workflows`:

```yaml
name: RTD workflows

on:
  pull_request:

jobs:
  rtd-docs-checks:
    uses: canonical/operator-workflows/.github/workflows/docs_rtd.yaml@main
    secrets: inherit
    with:
      python-version: '3.12'
```

If the repository does not already have a CLA check, copy `cla-check.yml` from the Sphinx Stack into `.github/workflows/`.

### Step 3 (global Step 3): Migrate the custom wordlist

Check for an existing custom wordlist in the following locations:
- `.custom_wordlist.txt` at the repository root
- `.vale/styles/config/vocabularies/local/accept.txt`

Migrate all found wordlist content to `docs/.custom_wordlist.txt` (append if multiple sources are found). If no wordlist exists, create a new `docs/.custom_wordlist.txt`. The old wordlist files at the root level may be removed.

Regardless of whether an existing wordlist was found, ensure the following entries are present in `docs/.custom_wordlist.txt` (add any that are missing):

```
AI
```

This is a common acronym that Vale would otherwise flag as errors.

> **Note (Sphinx Stack 2.0):** There is no committed `.vale.ini` to edit. `make vale` generates the Vale configuration into `docs/_dev/` at build time (via `docs/_dev/get_vale_conf.py`) and automatically appends `docs/.custom_wordlist.txt` to the accepted-terms list. Adding a term to `docs/.custom_wordlist.txt` is the only step needed to suppress spelling/terminology false positives. The old approach of adding a `[docs/reuse/mermaid.txt]` exclusion section to `.vale.ini` no longer applies, because `docs/reuse/` no longer exists and the generated `error.filter` already excludes the `Canonical.500-Repeated-words` and `Canonical.000-US-spellcheck` rules at error severity.

### Step 4 (global Step 4): Update `conf.py` with team-specific links

In Sphinx Stack 2.0, the site links live as keys inside the `html_context = {...}` dictionary in `docs/conf.py` (they are no longer top-level assignments). Locate the `html_context` dictionary and set the following keys:

| Key (inside `html_context`) | Value |
|---|---|
| `discourse` | `"https://discourse.charmhub.io"` |
| `mattermost` | `""` (empty string) |
| `matrix` | `"https://matrix.to/#/#charmhub-charmdev:ubuntu.com"` |

Separately, update the `intersphinx_mapping` dictionary. In Sphinx Stack 2.0 this ships commented out near the bottom of `conf.py` (with an example `snap` entry) — uncomment it and add the following entries:

```python
intersphinx_mapping = {
    "juju": ("https://documentation.ubuntu.com/juju/3.6/", None),
    "sphinx-stack": ("https://canonical-sphinx-stack.readthedocs-hosted.com/stable/", None),
}
```

> **Note:** Do **not** add the Matrix URL to `linkcheck_ignore` — the Sphinx Stack 2.0 `conf.py` already ignores all `matrix.to` links via the regex `r"https://matrix\.to/.*"`.

### Step 5 (global Step 5): Update project-specific variables in `conf.py`

Locate `charmcraft.yaml` (preferred) or `metadata.yaml` using the following procedure:

1. Look for `charmcraft.yaml` at the repository root.
2. If not found, search in immediate subdirectories (`*/charmcraft.yaml`).
3. If exactly one is found, use it.
4. If multiple are found, use a heuristic: prefer the one whose `name` field is the closest substring match to the repository name. In mono-repos, the primary charm typically shares its name with the repo (e.g., repo `content-cache-operator` → charm `content-cache` over `content-cache-backends-config`).
5. If the heuristic is inconclusive (no `name` matches, or multiple equally good matches), pick the first one alphabetically by directory path and proceed.
6. Whenever multiple files exist (regardless of which is selected), add a note to the PR description under "Items requiring human action" stating which `charmcraft.yaml` was selected and that the reviewer should verify the choice.

Apply the same fallback logic for `metadata.yaml`.

Extract the charm's `name` and `source` (GitHub URL) from the located file. Then update `conf.py`:

> **Note:** Even if `charmcraft.yaml` is found at the repo root, it may not contain `name` or `source`/`links.source` fields (this is common on `track/*` branches or older repos that pre-date the consolidated format). If those fields are absent, fall through to `metadata.yaml` as if `charmcraft.yaml` were not found.

- **`project`**: Set to the human-readable project name (e.g., `"WordPress charm"`). Ask the user for this value if it cannot be inferred. This is a top-level assignment in `conf.py`.
- **`product_page`** (key inside `html_context`): Set to `"charmhub.io/<charm-name>"` (derived from the `name` key in `charmcraft.yaml` / `metadata.yaml`).
- **`github_url`** (key inside `html_context`): Set to the GitHub repository URL (derived from `links.source` or `source` in `charmcraft.yaml` / `metadata.yaml`).
- **`source_edit_link`**: In Sphinx Stack 2.0 the `html_theme_options` block ships commented out. Uncomment it and set `source_edit_link` to the same GitHub repository URL. This renders an "Edit" button on RTD pages.

> **Note:** `product_page` and `github_url` are keys inside the `html_context = {...}` dictionary (the same dictionary edited in Step 4), not top-level assignments.

### Step 6 (global Step 6): Add the Mermaid extension

1. Add `sphinxcontrib-mermaid` to `docs/requirements.txt`.
2. Add `"sphinxcontrib.mermaid"` to the `extensions` list in `docs/conf.py`.
3. Find all `*.md` files under `docs/` (excluding `docs/_dev/` and `docs/_build/`) and replace Discourse-style Mermaid fences:
   - Change ` ```mermaid ` → ` ```{mermaid} `

### Step 7 (global Step 7): Pin all dependencies in `docs/requirements.txt`

All dependencies in `docs/requirements.txt` must be pinned to a specific version to ensure reproducible builds. Use `==` for exact version pins.

**Special case:** `myst-parser` must be pinned to exactly `4.0.1`. Sphinx Stack 2.0 ships this as `myst-parser~=4.0` — replace the `~=4.0` specifier with an exact pin:
```
myst-parser==4.0.1  # v5.0.0 causes version conflicts
```

For all other unpinned or loosely-pinned dependencies (e.g., those using `~=`, `>=`, or no version specifier at all), look up the latest available release on [PyPI](https://pypi.org/) and pin each to its latest version using `==`.

For example, entries from the Sphinx Stack's `requirements.txt` such as:
```
canonical-sphinx~=0.6
sphinx-autobuild
packaging~=26.1
```
…should each be pinned to their latest release, e.g.:
```
canonical-sphinx==0.6.0
sphinx-autobuild==2024.10.3
packaging==26.1
```

This also applies to `sphinxcontrib-mermaid`, which was added in Step 6.

> **Note:** The latest versions of each dependency will change over time. Always look up current versions on PyPI at the time of running this skill rather than relying on hardcoded versions in this document.

---

## Checkpoint

Commit all changes before proceeding to Phase 2 (`documentation-structure-builder`).

**Shared state to carry forward:**
- Charm name (from `charmcraft.yaml` / `metadata.yaml`)
- GitHub URL (from `links.source` or `source`)
- Human-readable project name (from Step 5)
- `newDomain` value (prompted from the user)
