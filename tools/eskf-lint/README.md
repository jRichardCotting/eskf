# eskf-lint

Conformance checker for ESKF v0.1 bundles. Zero dependencies, Python 3.8+.

```bash
python3 eskf_lint.py ./bundle
python3 eskf_lint.py ./bundle --strict   # warnings become errors
python3 eskf_lint.py ./bundle --json     # machine-readable, for CI
```

Exit codes: `0` conformant, `1` errors found, `2` bad invocation.

## What it checks

Each finding names the law it enforces.

| Code | Law | Check |
|---|---|---|
| E001 | L6 | Frontmatter block parses |
| E002 | L6 | `type` is present and non-empty (the one field OKF requires) |
| E003 | L5 | `id` is present |
| E004 | L6 | `eskf_version` is present |
| E005 | L5 | `id` matches the concept's path in the bundle |
| E006 | L1 | A `# Ledger` section exists |
| E009 | L3 | Every claim carries `source` and `writer` |
| E010 | L1 | No claim appears before a dated event heading |
| E011 | L1 | Event headings are ISO 8601 dates |
| E012 | L1 | Events are ordered newest first |
| E014 | L2 | `projection_of` is present and is an integer |
| E015 | L2 | **The projection is not stale**: `projection_of` equals the number of events in the ledger |
| E016 | L5 | Every cross-reference resolves to a concept in the bundle |
| E020 | L5 | The bundle has a `canon.md` at its root |
| W003 | L3 | The projection carries inline tier attribution |
| W004 | L6 | The declared `eskf_version` matches this linter |
| W006 | L1 | The ledger is not empty |
| W008 | L3 | Tiers are drawn from the known set |
| W011 | L3 | Event headings carry a source id |
| W015 | L2 | `projected_at` is present |

**E015 is the one that earns the tool.** Every other check catches a mistake at write time.
That one catches the failure OKF has no answer for: a knowledge base that looks perfectly
well-formed and is quietly out of date, which is the state most agent memory ends up in.

## In CI

```yaml
- run: python3 tools/eskf-lint/eskf_lint.py ./my-bundle --strict
```
