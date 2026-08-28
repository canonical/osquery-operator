---
name: documentation-finalizer
description: "Phase 3 of the documentation-project-creator skill. Creates the contribute page, updates Juju intersphinx links, updates the README and other repo files, and runs the QA loop (build, lint, Vale)."
---

# documentation-finalizer

**Prerequisites:** This is Phase 3 of the `documentation-project-creator` skill. Phases 1 and 2 must be complete. You should already have: the charm name, GitHub URL, human-readable project name, and `newDomain` value from earlier phases.

---

## Instructions

### Step 1 (global Step 17): Create the "How to contribute" page

Create `docs/how-to/contribute.rst`. If a file already exists at `docs/how-to/contribute.md`, delete it first.

The file must be written in reStructuredText. Copy the template from [`contribute-template.rst`](contribute-template.rst) in this skill directory, then apply the following placeholder substitutions:

| Placeholder | Source | Action |
|---|---|---|
| `__github_url__` | `links.source` or `source` in `charmcraft.yaml` / `metadata.yaml` | Replace automatically |
| `__charm_name__` | Charm name from `charmcraft.yaml` / `metadata.yaml` | Replace automatically |

Leave `TODO` comments in place for anything that requires human input.

After creating the file, open `docs/how-to/index.md` and verify that it contains a `toctree` entry for `contribute`. The entry must use the filename without the extension:

````markdown
```{toctree}
...
contribute
...
```
````

If the `toctree` contains a `contribute.md` entry, update it to `contribute`. If no entry exists for `contribute` at all, add one.

### Step 2 (global Step 18): Update Juju intersphinx links

Find all links to `documentation.ubuntu.com/juju` in the docs:

```bash
grep --exclude-dir=docs/_build -rn docs/ -e "documentation\.ubuntu\.com/juju"
```

For each match, determine the correct intersphinx target by looking up the corresponding page in the [`juju/juju` documentation source](https://github.com/juju/juju/tree/main/docs) and finding its MyST anchor target (the `(<target>)=` label at the top of the file).

Replace the URL-based link with an intersphinx reference using the `juju:` prefix:

```markdown
{ref}`Link text <juju:target_label>`
```

**Target lookup:** Refer to [`juju-intersphinx-targets.md`](juju-intersphinx-targets.md) in this skill directory for the URL-to-file mapping and known anchor targets. If you encounter a URL that maps to a page not listed there, fetch the target file from `juju/juju` and read its anchor label directly.

**Fallback:** If you cannot confidently identify the correct intersphinx target for a link, leave the original URL in place and prepend a `TODO` comment:

```markdown
<!-- TODO: Replace with intersphinx ref - could not find target for https://documentation.ubuntu.com/juju/... -->
[Link text](https://documentation.ubuntu.com/juju/...)
```

### Step 3 (global Step 19): Update the README

Verify all existing links in the README point to the RTD project URL. Then add a new `## Documentation` section:

````markdown
## Documentation

Our documentation is stored in the `docs` directory.
It is based on the Canonical Sphinx Stack
and hosted on [Read the Docs](https://about.readthedocs.com/). In structuring,
the documentation employs the [Diátaxis](https://diataxis.fr/) approach.

You may open a pull request with your documentation changes, or you can
[file a bug](LINK_TO_ISSUES) to provide constructive feedback or suggestions.

To run the documentation locally before submitting your changes:

```bash
cd docs
make run
```

GitHub runs automatic checks on the documentation
to verify spelling, validate links and style guide compliance.

You can (and should) run the same checks locally:

```bash
make spelling
make linkcheck
make vale
make lint-md
```
````

### Step 4 (global Step 20): Update other repository files

- **`.licenserc.yaml`**: Add the following to `paths-ignore` so that license checks do not run over the docs:
```yaml
paths-ignore:
  - '.readthedocs.yaml'
  - 'docs/**'
```
- **PR template**: Remove any mentions of Charmhub from the checklist.
- **Existing documentation workflows**: If the repository has a pre-existing `.github/workflows/docs.yaml` that calls `canonical/operator-workflows/.github/workflows/docs.yaml`, scope Vale to only `README.md` and `CONTRIBUTING.md` (whichever exist) by adding a `vale-files` input under `with:`. **Do not** add `paths:` trigger filters — those control when the workflow runs, not which files Vale checks, and removing them is not the right fix.

  ```yaml
  with:
    vale-files: '["README.md", "CONTRIBUTING.md"]'
  ```

  Only include files that actually exist in the repository. If neither `README.md` nor `CONTRIBUTING.md` is present, omit the `vale-files` input entirely.

  > **Note:** Only apply this scoping if the workflow's `uses:` value is `canonical/operator-workflows/.github/workflows/docs.yaml` (with any pin, e.g. `@main`). Workflows that call other `operator-workflows` paths (e.g., `docs_spread.yaml`, `docs_rtd.yaml`) are unrelated and should not be modified.

- **`pyproject.toml` codespell configuration**: If `pyproject.toml` contains a `[tool.codespell]` section, add `*/docs/_build/*` to the `skip` list. Use glob wildcards — codespell's `fnmatch`-based skip logic does not match plain directory names like `docs/_build`; the `*/` prefix ensures the pattern matches regardless of how codespell was invoked (absolute or relative path).

  ```toml
  [tool.codespell]
  skip = "...,*/docs/_build/*"
  ```

  The `docs/_build/` directory should be skipped because build artefacts contain many false positives. (Sphinx Stack 2.0 no longer ships a `docs/reuse/` directory, so there is no longer a `*/docs/reuse/*` pattern to add.)

### Step 5 (global Step 21): Fix build errors and Markdown linting errors

> **Important:** Run checks in this order: `make html` first (catches structural issues), then `make lint-md` (Markdown formatting), then `make vale` (style/spelling). Running linters before `make html` passes can produce confusing errors that are actually caused by structural issues.

> **Common pre-existing issues in Discourse-migrated docs:** The Sphinx Stack's strict build (`--fail-on-warning`) and lint tools often surface pre-existing quality issues that were not introduced by this skill. Check every file for: (a) skipped heading levels (H1 → H3 with no H2), (b) unclosed fenced code blocks (missing closing ` ``` `), and (c) bare domain names or technical terms like `juju.local` that Vale flags as capitalisation errors — wrap them in backticks.

> **Fix vs. flag for pre-existing issues:** Fix any issue in a file that this skill created or modified. For pre-existing issues in files the skill did **not** touch, prefer fixing simple mechanical problems that block the build or lint (unclosed code fences, skipped heading levels, trailing whitespace, hard tabs, missing blank lines around directives). Do **not** attempt substantive content rewrites of pre-existing documentation; if an issue would require rewording or restructuring prose, leave it in place and flag it in the PR description under "Items requiring human action" instead. The goal is a green build without silently rewriting authored content.

From the `docs/` directory, run:

```bash
make html
```

Read the full output carefully. For every error or warning reported, locate the offending file and line, fix the issue, and re-run `make html` until the build completes with no errors or warnings.

Common errors to look out for and how to fix them:

- **`toctree contains reference to nonexistent document`** — A file is listed in a `toctree` but does not exist. Either create the missing file or remove the entry from the `toctree`.
- **`duplicate label`** — Two files define the same MyST anchor target. Make the anchor in each file unique (see Phase 2 Step 7 for the naming convention).
- **`undefined label`** — A `{ref}` link points to an anchor that does not exist. Check the target name for typos or update it to match the correct anchor.
- **`image file not readable`** — An image referenced in a file cannot be found at the given path. Fix the path or copy the image to the correct location.
- **`WARNING: Title underline too short`** (RST files only) — Extend the underline to match the length of the title.

Once `make html` passes cleanly, run:

```bash
make lint-md
```

> **Note:** `make lint-md` requires `docs/_dev/.pymarkdown.json`, which ships in the `docs/_dev/` directory copied in Phase 1 Step 1. If `make lint-md` fails to find its configuration, verify that the entire `docs/_dev/` directory was copied.

Read the full output and fix every reported error. Common linting errors include:

- **Trailing whitespace** — Remove trailing spaces from the end of lines.
- **Missing blank line before/after a directive** — Add a blank line before and after MyST directive blocks (e.g., ` ```{note} `).
- **Hard tabs** — Replace tab characters with spaces.
- **Inconsistent heading hierarchy** — Ensure heading levels follow a consistent order within each file.

Re-run `make lint-md` after each round of fixes until it reports no errors.

Once `make lint-md` passes cleanly, also run:

```bash
make vale
```

Vale failures are blocking in CI, so it is important to catch them locally. Fix every reported **error** (severity `ERROR`). Warnings (severity `WARNING`) may be reviewed but do not need to block the PR.

> **Note (Sphinx Stack 2.0):** `make vale` generates its configuration into `docs/_dev/` at run time and automatically appends `docs/.custom_wordlist.txt` to the accepted-terms list. The generated `error.filter` already excludes the `Canonical.500-Repeated-words` and `Canonical.000-US-spellcheck` rules at error severity, so the Mermaid-related false positives that previously required a `docs/reuse/mermaid.txt` exclusion no longer occur (that directory no longer exists in 2.0).

Known category of Vale false positive to fix proactively:

- **`Canonical.007-Headings-sentence-case` on `AI usage`** in `contribute.rst` — caused by `AI` not being in the Vale vocabulary. This should already be suppressed by the `AI` entry added to `docs/.custom_wordlist.txt` in Phase 1 Step 3. If the error still appears, verify the wordlist entry is present.

> **Note:** Do not run `make spelling` or `make linkcheck` as part of this step — those checks require network access and should be run by a human before opening the pull request. Broken links reported by `make linkcheck` in CI may be pre-existing in the source documentation and are not necessarily introduced by this skill; flag them in the PR description for human review rather than attempting to fix them automatically.

Finally, if the repository uses codespell (i.e., `pyproject.toml` has a `[tool.codespell]` section), run from the **repository root** (not `docs/`):

```bash
codespell . --toml pyproject.toml
```

Ignore any errors from files that were not touched by this skill's work. False positives from `docs/_build/` should already be suppressed by the skip pattern added in Step 4. If they still appear, verify the glob patterns in `pyproject.toml`.
