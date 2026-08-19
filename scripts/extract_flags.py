#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Extract osquery flag definitions into CSV.

Each flag-defining macro expands to OSQUERY_FLAG(t, n, v, d, shell, external,
cli, hidden) (see osquery/include/osquery/flags.h). Those boolean bits fully
determine how a flag may be used, so the exported columns below are derived
systematically from the macro name:

  * ``cli``   -- the flag can only be set on the command line or in a flagfile,
                 never via the config "options" key.
  * ``shell`` -- the flag is only honoured by the interactive shell (osqueryi).

This script is committed alongside the charm so it can be re-run whenever the
OSQuery version is bumped, keeping the list of supported flags in sync with the
fork's source. See ``docs/reference/configurations.rst`` for how the output maps
to charm configuration options.
"""

import argparse
import csv
import re
from pathlib import Path

# Flag-defining macros mapped to the (cli, shell) bits that the macro sets when
# it expands to OSQUERY_FLAG. Only these two bits are needed to derive the
# exported columns; ``external``/``hidden`` do not affect them.
MACROS = {
    #                cli,   shell
    "FLAG": (False, False),
    "SHELL_FLAG": (False, True),
    "EXTENSION_FLAG": (False, False),
    "HIDDEN_FLAG": (False, False),
    "CLI_FLAG": (True, False),
}

# Plugin-selection flags follow the ``<name>_plugin`` / ``<name>_plugins`` naming
# convention (e.g. config_plugin, logger_plugin, distributed_plugin).
PLUGIN_RE = re.compile(r"_plugins?$")

# Matches FLAG(type, name, default, "description"), possibly spread over lines.
# ``type`` and ``name`` are plain identifiers; ``default`` is captured lazily and
# is anchored by the trailing quoted description. Requiring that description also
# skips the macros' own ``#define FLAG(t, n, v, d)`` lines, which have no string.
STRING = r'"(?:[^"\\]|\\.)*"'
SEP = r"(?:\s|//[^\n]*|/\*.*?\*/)*"  # whitespace and C/C++ comments between tokens
FLAG_RE = re.compile(
    r"\b(" + "|".join(MACROS) + r")" + SEP + r"\(" + SEP
    + r"(\w+)" + SEP + r"," + SEP  # type
    + r"(\w+)" + SEP + r"," + SEP  # name
    + r"(.+?)" + SEP + r"," + SEP  # default (lazy)
    + r"(?:" + STRING + SEP + r")+\)",  # description (one or more string literals)
    re.DOTALL,
)

SOURCE_SUFFIXES = {".h", ".hpp", ".hh", ".c", ".cc", ".cxx", ".cpp", ".mm", ".m"}
SKIP_DIRS = {".git", "third-party", "build", "cmake-build-debug", "cmake-build-release"}


def extract(text, path):
    """Yield one record per flag definition found in ``text``."""
    for m in FLAG_RE.finditer(text):
        macro, ftype, name, default = m.groups()
        cli, shell = MACROS[macro]
        yield {
            "name": name,
            "type": ftype,
            "default": default.strip(),
            # A flag is "related to a plugin" when it selects a registry plugin,
            # which by convention is named ``<name>_plugin(s)``.
            "is_plugin": bool(PLUGIN_RE.search(name)),
            # A flag can be pushed remotely by a TLS controller only if it may be
            # set through the config "options" key, i.e. it is not CLI-only.
            "is_configurable_remotely_using_tls": not cli,
            # Shell flags are only honoured by the interactive shell (osqueryi);
            # every other flag applies when running as a daemon.
            "applies_in_daemon_mode": not shell,
            "file": path,
            "line": text.count("\n", 0, m.start()) + 1,
        }


def main():
    """Parse arguments, scan the source tree and write the CSV."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", type=Path, help="Repository root to scan")
    parser.add_argument("--output", default="flags.csv", type=Path, help="Output CSV path")
    args = parser.parse_args()

    root = args.root.resolve()
    files = (
        p
        for p in root.rglob("*")
        if p.suffix in SOURCE_SUFFIXES and not SKIP_DIRS.intersection(p.parts)
    )

    rows = [
        row
        for path in files
        for row in extract(path.read_text(errors="ignore"), str(path.relative_to(root)))
    ]
    rows.sort(key=lambda r: (r["name"], r["file"], r["line"]))

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "type",
                "default",
                "is_plugin",
                "is_configurable_remotely_using_tls",
                "applies_in_daemon_mode",
                "file",
                "line",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
