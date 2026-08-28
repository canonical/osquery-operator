---
name: documentation-structure-builder
description: "Phase 2 of the documentation-project-creator skill. Structures and refactors documentation content: index pages, landing pages, URL-rewrite script, reference anchors, internal links, and MyST conversion."
---

# documentation-structure-builder

**Prerequisites:** This is Phase 2 of the `documentation-project-creator` skill. Phase 1 (`documentation-project-setup`) must be complete. You should already have: the charm name, GitHub URL, human-readable project name, and `newDomain` value from Phase 1.

---

## Instructions

### Step 1 (global Step 8): Ensure `docs/index.md` exists

If `docs/index.md` does not exist, create it with the following minimal content:

```markdown
# Documentation

TODO: update

# Contents
```

If `docs/index.md` already exists, verify that the first non-frontmatter line is an H1 heading (a line starting with `# `). If the file starts with H2 or lower, add an H1 heading as the first non-frontmatter line. Sphinx will warn `Document headings start at H2, not H1`, and with `--fail-on-warning` this aborts the build.

### Step 2 (global Step 9): Create or update subdirectory landing pages

For every subdirectory under `docs/` (excluding `docs/_dev/`, `docs/_templates/`, and `docs/_build/`), handle the two cases below.

#### Case A: No index file exists

If neither `index.md` nor `index.rst` is present, create a new `index.md` with the following structure:

````markdown
---
myst:
  html_meta:
    "description lang=en": "TBD"
---

(<directory_name_with_underscores>)=

# <Directory Name>

Description TBD

```{toctree}
:maxdepth: 1
<list of .md files in this directory>
```
````

#### Case B: An index file already exists

If `index.md` or `index.rst` already exists, **do not replace or delete the file**. Instead, make only the following targeted additions to the existing file if they are not already present:

1. **H1 heading** — Verify that the first non-frontmatter line is an H1 heading (a line starting with `# ` in Markdown, or a title with `===` underline in RST). If the file starts with H2 or lower, add an H1 heading as the first non-frontmatter line. Sphinx will warn `Document headings start at H2, not H1`, and with `--fail-on-warning` this aborts the build.

2. **Anchor target** — If the file does not already contain a `(<directory_name_with_underscores>)=` label, add it near the top of the file (after any front-matter block, before the first heading). The label format follows the same convention as Step 7:
   - Strip the `docs/` prefix
   - Replace `/` and `-` with `_`
   - Example: `docs/how-to/` → `(how_to_index)=`

3. **`toctree` directive** — If the file does not already contain a `toctree` directive, append one at the end of the file listing the `.md` and `.rst` files in that subdirectory (excluding the index file itself):
   ````markdown
   ```{toctree}
   :maxdepth: 1
   <list of files in this directory, without extensions>
   ```
   ````
   For `.rst` files, use the equivalent RST directive instead:
   ```rst
   .. toctree::
      :maxdepth: 1

      <list of files in this directory, without extensions>
   ```

If the anchor target or `toctree` already exists in the file, leave them as-is.

> **Existing manual navigation:** If the file already provides its own navigation as a manual list of links (e.g., a numbered or bulleted list of links to the pages in the section), do **not** duplicate that navigation with a visible `toctree`. A `toctree` is still required so Sphinx knows the document hierarchy and to avoid `document isn't included in any toctree` warnings, but make it hidden by adding the `:hidden:` option:
>
> ````markdown
> ```{toctree}
> :hidden:
> :maxdepth: 1
> <list of files in this directory, without extensions>
> ```
> ````
>
> This keeps the curated manual list as the visible navigation while satisfying the toctree requirement.

### Step 3 (global Step 10): Refactor the `docs/index.md` home page

1. Add an SEO metadata block to the very top of the file:
   ```markdown
   ---
   myst:
     html_meta:
       "description lang=en": "TBD"
   ---
   ```
2. Replace the existing `# Contents` section (and everything below it) with a MyST `toctree` directive:
   ````markdown
   ```{toctree}
   :hidden:
   tutorial/index
   how-to/index
   reference/index
   explanation/index
   release-notes/index
   ```
   ````
   - If a changelog exists but no release notes, include it directly in the home page `toctree`.
   - If both a changelog and release notes exist, include the changelog in `docs/reference/index.md` instead.
   - If the tutorial is a single file directly in `docs/` with no subdirectory (e.g., `docs/tutorial.md`), include it as `Tutorial <tutorial-file-name>` to preserve Diátaxis terminology. If a `docs/tutorial/` subdirectory exists — even if it contains only one file — use the standard `tutorial/index` toctree entry and create `tutorial/index.md` per Step 2.

### Step 4 (global Step 11): Update HTML metadata descriptions on `index.md` files

All `index.md` files created or updated in Steps 1–3 contain a placeholder metadata description:

```markdown
---
myst:
  html_meta:
    "description lang=en": "TBD"
---
```

Replace each `"TBD"` value with a concise, meaningful one-sentence description appropriate to the section. Use the charm name (from `charmcraft.yaml` / `metadata.yaml`) to make the descriptions specific to the project.

Use the following templates as a starting point, substituting `<charm name>` with the human-readable project name:

| File | Description template |
|---|---|
| `docs/index.md` | `"Learn how to deploy, configure and operate the <charm name> using Juju."` |
| `docs/tutorial/index.md` | `"Follow step-by-step tutorials to get started with the <charm name>."` |
| `docs/how-to/index.md` | `"How-to guides for operating the <charm name>, including basic operations, upgrades, and deployments."` |
| `docs/reference/index.md` | `"Technical reference documentation for the <charm name>, including actions, configurations, and architecture."` |
| `docs/explanation/index.md` | `"Explanations of key concepts for the <charm name>."` |
| `docs/release-notes/index.md` | `"Release notes for the <charm name>."` |

For any subdirectory `index.md` files not listed above, write a description that summarises the purpose of that section in the context of the charm.

### Step 5 (global Step 12): Set up the cookie banner for Google Analytics

The `header.html` and `footer.html` templates required for the cookie banner are included in `docs/_templates/` — these were copied from the Sphinx Stack in Phase 1 Step 1, so no additional files need to be sourced. The cookie banner CSS and JS are served remotely from `assets.ubuntu.com`.

In Sphinx Stack 2.0, `docs/conf.py` ships `templates_path`, `html_css_files`, and `html_js_files` commented out. **Uncomment** them and set the values below. All three settings must be configured together — `templates_path` enables the cookie banner templates, which in turn reference the remote CSS and JS files:

```python
templates_path = ["_templates"]

html_css_files = ["https://assets.ubuntu.com/v1/d86746ef-cookie_banner.css"]

html_js_files = ["https://assets.ubuntu.com/v1/287a5e8f-bundle.js"]
```

> **Note:** Ensure `templates_path` is set to `["_templates"]` specifically. The `html_css_files` and `html_js_files` values must use the remote `assets.ubuntu.com` URLs above, not local file paths.

### Step 6 (global Step 13): Add the URL-rewrite script

All documentation projects must include a URL-rewrite script that maps the RTD-hosted domain to the canonical public URL. This script lives in `docs/_static/js/overwrite_links.js`.

1. Create the directory `docs/_static/js/` if it does not already exist.
2. Prompt the user for the `newDomain` value — this is the canonical URL where the documentation will be served (e.g., `canonical.com/juju/docs/charm-name`). The value must **not** include `https://` and must **not** end with a trailing `/`.
3. Create `docs/_static/js/overwrite_links.js` with the content in `overwrite_links.js`, substituting `<<NewURL>>` with the user-provided `newDomain` value.

> **Note:** Leave `<<RtDURL>>` as the `oldDomain` value — this placeholder cannot be set until after the RTD project has been created and the RTD-hosted URL is known. It will be updated as a post-creation human action item.

4. In `docs/conf.py`, uncomment `html_static_path` (it ships commented out in Sphinx Stack 2.0). Ensure it is set to:

```python
html_static_path = ["_static"]
```

5. Append the local script path to the `html_js_files` list configured in Step 5. The final value should be:

```python
html_js_files = [
    "https://assets.ubuntu.com/v1/287a5e8f-bundle.js",
    "js/overwrite_links.js",
]
```

### Step 7 (global Step 14): Add reference targets to all documentation files

For every `*.md` file under `docs/` (excluding `index.md` files), prepend a MyST anchor target. The target format is derived from the file's relative path:

- Strip the `docs/` prefix and `.md` suffix
- Replace `/`, spaces, and `-` with `_`
- Wrap in `(<name>)=`

**Examples:**
- `docs/how-to/upgrade.md` → `(how_to_upgrade)=`
- `docs/reference/actions.md` → `(reference_actions)=`
- `docs/explanation/charm-architecture.md` → `(explanation_charm_architecture)=`

For `index.md` files in subdirectories, the same convention applies:
- `docs/tutorial/index.md` → `(tutorial_index)=`

### Step 8 (global Step 15): Update internal links

Update any links pointing to the old Charmhub documentation pages to use the new MyST target headers instead of direct URLs. Use this format:

```markdown
{ref}`Link text <target_header>`
```

**Do not** use direct URL links (e.g., `https://documentation.ubuntu.com/charm-name/latest/how-to/`) as they are fragile.

Links to auto-generated Charmhub content (e.g., `https://charmhub.io/charm-name/actions`) may remain in place.

### Step 9 (global Step 16): Update Markdown to MyST syntax

Review all `*.md` files and update Discourse Markdown to MyST Markdown:

- **Mermaid blocks**: Already handled in Phase 1 Step 6.
- **Admonition blocks**: Convert `[note]` blocks and `>` blockquote-style notes to MyST:
  ````markdown
  ```{note}
  Your note here.
  ```
  ````
- **Admonitions containing code blocks**: Use four backticks to fence the admonition:
  `````markdown
  ````{note}
  Here's a code example:
  ```
  echo "Hello"
  ```
  ````
  `````

---

## Checkpoint

Commit all changes before proceeding to Phase 3 (`documentation-finalizer`).
