# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning follows the spec, not
the tools: `<major>.<minor>`, minor being backward compatible.

## [0.1] - 2026-07-14

First public release. Draft.

### Added
- `SPEC.md`: the six laws, ledger, projection, claims, tiers, canon, writer, erasure,
  conformance, relationship to OKF.
- `examples/minimal-bundle/`: a conformant seven-concept bundle.
- `tools/eskf-lint/`: zero-dependency conformance checker.

### Notes
- Strict superset of OKF v0.1. Any OKF consumer reads an ESKF bundle without modification.
- Four tiers defined (`observed`, `public-record`, `inferred`, `self-declared`). Producers
  may extend the list and must not collapse the distinction.
