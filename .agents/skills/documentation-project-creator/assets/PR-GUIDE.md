# PR description: review guide

This skill produces PRs with many added or modified files. To help human reviewers focus their attention, include a `## For reviewers` section in the PR description, placed **before** the `## Items requiring human action` section.

**Only list files that were actually added or modified in the current run.** Omit rows for files that do not apply to this particular repository.

Organize the files into three priority tiers:

## High priority — verify correctness

These files contain project-specific values, generated content, or prose changes that require human judgment. List each applicable file with a brief note explaining what was changed:

| File | What to verify |
|---|---|
| `docs/conf.py` | Project name, `product_page`, `github_url`, `source_edit_link`, intersphinx mappings, cookie banner settings, URL-rewrite script (Steps 4, 5, 6, 12, 13) |
| `docs/_static/js/overwrite_links.js` | Verify `newDomain` substitution is correct; `oldDomain` is expected to be `<<RtDURL>>` placeholder — updated post-RTD-creation (Step 13) |
| `docs/index.md` | Home page structure, toctree entries, metadata description (Steps 8, 10, 11) |
| `docs/how-to/contribute.rst` | Template with `TODO` comments and auto-substituted `__github_url__` (Step 17) |
| `docs/*/index.md` (newly created) | Generated content: descriptions, toctree entries, anchor targets (Step 9 Case A, Step 11). Mark as *"(new file — review all content)"* |
| `docs/*/index.md` (modified existing) | Targeted additions only: toctree, anchor target, H1 heading (Step 9 Case B). Mark as *"(existing file — toctree/anchor/heading additions only)"* |
| Existing `*.md` files with content changes | Internal link updates (Step 15), MyST syntax conversions (Step 16), Juju intersphinx replacements (Step 18) |
| `README.md` | New `## Documentation` section (Step 19) |

## Medium priority — structural and CI changes

These files follow predictable patterns but affect CI behavior or build configuration:

| File | What to verify |
|---|---|
| `.github/workflows/docs_rtd.yaml` | New workflow calling `operator-workflows` (Step 2) |
| `.github/workflows/docs.yaml` | `vale-files` scoping added, if this workflow existed (Step 20) |
| `docs/requirements.txt` | Version pins from PyPI lookups (Step 7) |
| `.licenserc.yaml` | `paths-ignore` additions for docs (Step 20) |
| `pyproject.toml` | Codespell skip patterns (Step 20) |
| `.github/pull_request_template.md` | Charmhub references removed, if applicable (Step 20) |

## Low priority — copied from the Sphinx Stack

These files are copied verbatim from the [Sphinx Stack](https://github.com/canonical/sphinx-stack) and should not deviate from upstream. Wrap them in a collapsed `<details>` block in the PR description:

```markdown
<details>
<summary>Low priority — copied verbatim from the Sphinx Stack (click to expand)</summary>

- `.readthedocs.yaml`
- `docs/.gitignore`
- `docs/Makefile`
- `docs/_dev/*`
- `docs/_templates/*`
- `.github/workflows/cla-check.yml` (if added)
- `docs/redirects.txt`
- `docs/.custom_wordlist.txt`

These files should not need review unless upstream deviations are suspected.

</details>
```

Anchor-only additions to `*.md` files (Step 14 — the mechanical prepend of `(<name>)=` targets) are also low priority and can be listed here or omitted entirely.

---

## Items requiring human action

The section above covers where to focus review attention on the PR diff. This section covers tasks that require human judgment or actions outside the repository and **cannot be automated**. Include these tasks in the description of the PR so human contributors have a record of action items:

1. **Setting up the RTD project in the Read the Docs backend** ([app.readthedocs.com](https://app.readthedocs.com/organizations/canonical/)):
   - Organization and team: "Canonical / Platform Engineering"
   - Project name schema: `<Software name> <K8s, if applicable> charm`
   - URL versioning scheme: Single version without translations
   - Set the default branch to your working branch initially (switch to `main` after the PR is merged)
   - Privacy level: `Private` during setup, `Public` when ready
   - Enable "Build pull requests for this project" (Privacy level: `Public`)
   - Add the project as a subproject of the "Ubuntu documentation library" project (may require a Technical Author)

2. **Update the `documentation` key in `charmcraft.yaml` or `metadata.yaml` once the URL is known**.

3. **Update `conf.py` once the URL is known**

   Once the RTD project has been created in the Read the Docs backend and the URL is known, update the following in `conf.py`:

   - **`ogp_site_url`**: Set to the RTD project URL.
   - **`slug`**: Uncomment and set to the RTD project slug.

4. **Set up the project so that the URL is under the Canonical domain**:

   - **Update `oldDomain` in `docs/_static/js/overwrite_links.js`**: Once the RTD project has been created and the RTD-hosted URL is known, replace the `<<RtDURL>>` placeholder with the actual RTD domain (e.g., `charm-name.readthedocs-hosted.com`). The value must **not** include `https://` and must **not** end with a trailing `/`.
   - **Update the HAProxy configuration**: Submit a merge request into [rtd-proxy-config](https://code.launchpad.net/rtd-proxy-config) to update the staging environment (`staging/haproxy.cfg`). Once this merge request is approved, validate the changes in the staging environment (`staging.canonical.com`). Once the changes are validated, submit a merge request into rtd-proxy-config to update the production environment (`prod/haproxy.cfg`). **Note**: These steps can happen after this PR is merged, but it's helpful to start them ASAP in case there are issues with `docs/_static/js/overwrite_links.js` or any relevant variables in `docs/conf.py`.

5. **Confirming `ogp_site_url` and `slug`** in `conf.py` with a Technical Author before the PR is merged.

6. **Verifying the cookie banner** before opening the pull request:
   ```bash
   cd docs
   make clean
   make install
   make run
   ```
   Open the rendered documentation in an incognito browser window and confirm that the cookie consent banner appears and functions correctly.

7. **Running the remaining quality checks** before opening the pull request:
   ```bash
   cd docs
   make run        # Check for rendering issues
   make spelling   # Fix spelling errors
   make linkcheck  # Fix broken links
   make vale       # Fix style errors
   ```

8. **Reviewing the "How to contribute" page** (`docs/how-to/contribute.rst`) for any remaining `TODO` comments and completing them.

9. **Verify `charmcraft.yaml` selection (mono-repos only)**: If the repository contains multiple `charmcraft.yaml` or `metadata.yaml` files (e.g., in a mono-repo), the automated process selects one using a heuristic (see Step 5). Verify that the correct file was used for deriving project-specific variables (`project`, `product_page`, `github_url`, etc.) in `conf.py`.

10. **Post-merge steps**:
    - Update the RTD project backend to use `main` as the Default branch.
    - Set the Default version to "Public".
    - Promote the charm to stable on Charmhub.
    - Update the repository's configuration in [`canonical-repo-automation`](https://github.com/canonical/canonical-repo-automation) to set documentation checks as required (spelling, links, inclusive language).
