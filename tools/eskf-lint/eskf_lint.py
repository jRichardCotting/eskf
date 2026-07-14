#!/usr/bin/env python3
# Copyright 2026 The ESKF Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
eskf-lint: conformance checker for Event-Sourced Knowledge Format bundles.

    python3 eskf_lint.py ./bundle
    python3 eskf_lint.py ./bundle --strict   # warnings become errors
    python3 eskf_lint.py ./bundle --json     # machine-readable

Exit codes: 0 conformant, 1 errors found, 2 bad invocation.
Zero dependencies. Standard library only, Python 3.8+.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

ESKF_VERSION = "0.1"
KNOWN_TIERS = {"observed", "public-record", "inferred", "self-declared"}
RESERVED = {"index.md", "log.md"}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)
EVENT_RE = re.compile(r"^##\s+(\S+)(?:\s*\u00b7\s*(.+?))?\s*$")
CLAIM_RE = re.compile(r"^-\s+\*\*\[([^\]]+)\]\*\*\s*(.*)$")
META_RE = re.compile(r"^\s*`(.+)`\s*$")
LINK_RE = re.compile(r"\[[^\]]*\]\((/[^)\s]+\.md)\)")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIER_INLINE_RE = re.compile(r"\[(" + "|".join(sorted(KNOWN_TIERS)) + r")\s*\u00b7")


def parse_frontmatter(text):
    """Return (frontmatter_dict, body), or (None, text) when absent.

    Parses only the YAML subset the spec uses: scalars and inline lists. A bundle
    that needs more than this is doing too much work in frontmatter.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    raw, body = m.group(1), m.group(2)
    fm = {}
    for line in raw.split("\n"):
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            fm[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
        else:
            fm[key] = value.strip("'\"")
    return fm, body


def split_sections(body):
    """Split a body into its top-level '# Heading' sections."""
    sections, current, buf = {}, None, []
    for line in body.split("\n"):
        if line.startswith("# "):
            if current is not None:
                sections[current] = "\n".join(buf)
            current, buf = line[2:].strip(), []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf)
    return sections


@dataclass
class Finding:
    level: str
    code: str
    path: str
    line: int
    message: str


@dataclass
class Report:
    findings: List[Finding] = field(default_factory=list)
    concepts: int = 0
    events: int = 0
    claims: int = 0

    def error(self, code, path, line, message):
        self.findings.append(Finding("error", code, path, line, message))

    def warn(self, code, path, line, message):
        self.findings.append(Finding("warning", code, path, line, message))

    @property
    def errors(self):
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self):
        return [f for f in self.findings if f.level == "warning"]


def collect_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".md"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def concept_id_of(root, path):
    return os.path.relpath(path, root)[:-3].replace(os.sep, "/")


def lint_bundle(root):
    rep = Report()
    files = collect_files(root)
    if not files:
        rep.error("E000", root, 0, "no markdown files found, this is not a bundle")
        return rep

    present: Set[str] = {concept_id_of(root, p) for p in files}
    referenced = []

    if not os.path.exists(os.path.join(root, "canon.md")):
        rep.error("E020", "canon.md", 0, "L5: bundle has no canon.md at its root")

    for path in files:
        name = os.path.basename(path)
        rel = os.path.relpath(path, root)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        lines = text.split("\n")

        for i, line in enumerate(lines):
            for target in LINK_RE.findall(line):
                referenced.append((target.lstrip("/")[:-3], rel, i + 1))

        if name in RESERVED:  # OKF-reserved, carries no frontmatter
            continue

        rep.concepts += 1
        fm, body = parse_frontmatter(text)

        # --- L6: OKF conformance ---
        if fm is None:
            rep.error("E001", rel, 1, "L6: no parseable YAML frontmatter block")
            continue
        if not fm.get("type"):
            rep.error("E002", rel, 1, "L6: frontmatter is missing the required 'type' field")

        # --- L5: identity ---
        cid = fm.get("id")
        if not cid:
            rep.error("E003", rel, 1, "L5: frontmatter is missing 'id' (canonical id)")
        elif cid != concept_id_of(root, path):
            rep.error("E005", rel, 1, "L5: id '%s' does not match its path, expected '%s'"
                      % (cid, concept_id_of(root, path)))

        ver = fm.get("eskf_version")
        if not ver:
            rep.error("E004", rel, 1, "frontmatter is missing 'eskf_version'")
        elif str(ver) != ESKF_VERSION:
            rep.warn("W004", rel, 1, "declares eskf_version '%s', this linter targets %s"
                     % (ver, ESKF_VERSION))

        sections = split_sections(body)

        # --- L1: the ledger ---
        if "Ledger" not in sections:
            rep.error("E006", rel, 1, "L1: concept has no '# Ledger' section")
            continue

        offset = next((i for i, ln in enumerate(lines) if ln.strip() == "# Ledger"), 0)
        events, claims, dates = 0, 0, []
        pending_line, pending_meta = None, False

        for i, line in enumerate(sections["Ledger"].split("\n")):
            lineno = offset + i + 2

            m = EVENT_RE.match(line)
            if m:
                if pending_line and not pending_meta:
                    rep.error("E009", rel, pending_line, "L3: claim has no metadata line")
                pending_line, pending_meta = None, False
                events += 1
                date = m.group(1)
                if ISO_DATE_RE.match(date):
                    dates.append(date)
                else:
                    rep.error("E011", rel, lineno,
                              "L1: event heading '%s' is not an ISO 8601 date (YYYY-MM-DD)" % date)
                if not m.group(2):
                    rep.warn("W011", rel, lineno, "L3: event heading carries no source id")
                continue

            m = CLAIM_RE.match(line)
            if m:
                if pending_line and not pending_meta:
                    rep.error("E009", rel, pending_line, "L3: claim has no metadata line")
                claims += 1
                pending_line, pending_meta = lineno, False
                tier = m.group(1).strip()
                if tier not in KNOWN_TIERS:
                    rep.warn("W008", rel, lineno, "L3: unknown tier '%s', known tiers are %s"
                             % (tier, ", ".join(sorted(KNOWN_TIERS))))
                if events == 0:
                    rep.error("E010", rel, lineno, "L1: claim appears before any dated event")
                continue

            m = META_RE.match(line)
            if m and pending_line:
                kv = {}
                for part in m.group(1).split("\u00b7"):
                    if ":" in part:
                        k, _, v = part.partition(":")
                        kv[k.strip()] = v.strip()
                for required in ("source", "writer"):
                    if not kv.get(required):
                        rep.error("E009", rel, lineno,
                                  "L3: claim metadata is missing '%s'" % required)
                pending_meta = True

        if pending_line and not pending_meta:
            rep.error("E009", rel, pending_line, "L3: claim has no metadata line")

        rep.events += events
        rep.claims += claims

        if events == 0:
            rep.warn("W006", rel, 1, "L1: ledger section is present but empty")
        if dates != sorted(dates, reverse=True):
            rep.error("E012", rel, offset + 1, "L1: events are not ordered newest first")

        # --- L2: the projection replays the whole ledger ---
        if "Projection" not in sections:
            rep.warn("W007", rel, 1, "L2: concept has a ledger and no '# Projection' section")
            continue

        declared = fm.get("projection_of")
        if declared is None:
            rep.error("E014", rel, 1,
                      "L2: frontmatter is missing 'projection_of' (events replayed)")
        else:
            try:
                declared_n = int(str(declared))
            except ValueError:
                rep.error("E014", rel, 1, "L2: 'projection_of' is not an integer")
            else:
                if declared_n != events:
                    rep.error("E015", rel, 1,
                              "L2: projection is stale, it replays %d event(s) and the ledger holds %d"
                              % (declared_n, events))
        if not fm.get("projected_at"):
            rep.warn("W015", rel, 1, "L2: frontmatter is missing 'projected_at'")
        if sections["Projection"].strip() and not TIER_INLINE_RE.search(sections["Projection"]):
            rep.warn("W003", rel, 1, "L3: projection carries no inline tier attribution")

    for target, rel, lineno in referenced:
        if target not in present:
            rep.error("E016", rel, lineno,
                      "L5: reference to '%s' does not resolve to a concept in this bundle" % target)

    return rep


BOLD, RED, YELLOW, GREEN, DIM, RESET = (
    ("\033[1m", "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m")
    if sys.stdout.isatty() else ("", "", "", "", "", "")
)


def render(rep, strict):
    for f in rep.findings:
        color = RED if f.level == "error" else YELLOW
        print("%s%s%s %s%s%s  %s:%d  %s"
              % (color, f.level.upper(), RESET, DIM, f.code, RESET, f.path, f.line, f.message))

    n_err, n_warn = len(rep.errors), len(rep.warnings)
    print()
    print("%s%d concepts, %d events, %d claims%s"
          % (DIM, rep.concepts, rep.events, rep.claims, RESET))

    if n_err == 0 and not (strict and n_warn):
        tail = "" if n_warn == 0 else " (%d warning%s)" % (n_warn, "" if n_warn == 1 else "s")
        print("%s%sCONFORMANT%s with ESKF v%s%s" % (GREEN, BOLD, RESET, ESKF_VERSION, tail))
        return 0

    print("%s%sNOT CONFORMANT%s with ESKF v%s: %d error%s, %d warning%s"
          % (RED, BOLD, RESET, ESKF_VERSION,
             n_err, "" if n_err == 1 else "s",
             n_warn, "" if n_warn == 1 else "s"))
    return 1


def main():
    ap = argparse.ArgumentParser(
        prog="eskf-lint",
        description="Check a bundle against the six laws of ESKF v0.1.")
    ap.add_argument("bundle", help="path to the bundle root")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    args = ap.parse_args()

    if not os.path.isdir(args.bundle):
        print("eskf-lint: '%s' is not a directory" % args.bundle, file=sys.stderr)
        return 2

    rep = lint_bundle(args.bundle)

    if args.as_json:
        ok = not rep.errors and not (args.strict and rep.warnings)
        print(json.dumps({
            "eskf_version": ESKF_VERSION,
            "bundle": args.bundle,
            "conformant": ok,
            "concepts": rep.concepts,
            "events": rep.events,
            "claims": rep.claims,
            "findings": [f.__dict__ for f in rep.findings],
        }, indent=2))
        return 0 if ok else 1

    return render(rep, args.strict)


if __name__ == "__main__":
    sys.exit(main())
