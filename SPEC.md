# ESKF: Event-Sourced Knowledge Format

**Version 0.1**

ESKF is an open format for organizational memory that stays correct over time.

A knowledge base for agents is easy to create and hard to keep true. The failure is never the first week. It is month six, when the base has absorbed a hundred writes from a dozen sources, half of them inferences, and nobody can tell which sentence came from a recorded interview and which one came from a model guessing on a Tuesday.

ESKF is built around one idea borrowed from a well understood corner of systems engineering: **the log is the truth, and everything else is a projection of it.**

An ESKF bundle is a conformant [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundle. Any OKF consumer can read it without modification.

---

## 1. Motivation

The LLM wiki pattern, popularized in April 2026, established that a folder of interlinked markdown files outperforms a vector database for agent memory at organizational scale. The knowledge is compiled once instead of being rediscovered on every query, and it accumulates.

In June 2026, Google Cloud published OKF v0.1, which formalized that pattern into a portable specification: a directory of markdown files with YAML frontmatter, one required field, links forming the graph.

OKF specifies the artifact. It states, as an explicit non-goal, that it does not prescribe how knowledge is produced, maintained, or kept honest. That is left entirely to the producer.

Three failure modes live in that gap, and every team building agent memory hits all three.

**Rot.** OKF has a `timestamp` field. A field is not a process. Nothing in the format regenerates anything. A shared bundle with no maintenance process goes stale in weeks, and agents keep answering from it with total confidence.

**Drift.** Agents writing markdown at scale produce broken links, duplicate concepts, mangled frontmatter. The OKF answer is to require every consumer to tolerate the mess. Tolerance keeps the reader from crashing. It does nothing for the reader that is trying to be right.

**Laundering.** When a professor's hypothesis, a public record, and a self-reported claim all become a paragraph of prose in the same file, the next reader sees three facts. One write of an inference becomes institutional truth three weeks later, read by someone who was never in the room.

ESKF closes those three gaps with six invariants and one architectural commitment.

---

## 2. The Six Laws

| # | Law | Failure prevented |
|---|---|---|
| **L1** | The ledger is append-only, dated, and immutable. | Loss of history |
| **L2** | The projection is regenerated from the full ledger and never appended to. | Rot |
| **L3** | Every claim carries provenance and an epistemic tier. | Laundering |
| **L4** | Writes go through a single writer and accept structured claims only. | Drift |
| **L5** | Every reference resolves to a canonical id. | Silent graph fragmentation |
| **L6** | The output remains OKF conformant. | Lock-in |

Everything below is the mechanics of enforcing these six.

---

## 3. Terminology

- **Bundle.** A directory tree of markdown concepts. The unit of distribution. Inherited from OKF.
- **Concept.** One entity, one markdown file. Inherited from OKF.
- **Ledger.** The append-only, dated event log inside a concept. The source of truth for that concept.
- **Event.** One dated entry in a ledger. Carries one or more claims. Immutable once written.
- **Claim.** The atomic unit of assertion. Structured, typed, sourced, tiered.
- **Tier.** The epistemic strength of a claim.
- **Projection.** The derived, human-readable synthesis of a concept, computed from its ledger. Disposable by construction.
- **Replay.** Regenerating a projection from the full ledger.
- **Canon.** The registry of canonical ids and their aliases.
- **Writer.** The single process authorized to modify a bundle.
- **Source.** A raw artifact (transcript, PDF, record) referenced by the ledger and stored outside the bundle.

---

## 4. Concept Documents

An ESKF concept is an OKF concept with two conventional body sections and a small set of additional frontmatter fields.

```markdown
---
type: Student                          # REQUIRED (OKF)
id: student/mariana-costa              # REQUIRED (ESKF): canonical id
eskf_version: "0.1"                    # REQUIRED (ESKF)
title: Mariana Costa
aliases: [Mariana C., M. Costa]
projection_of: 3                       # events replayed into the current projection
projected_at: 2026-05-18T14:02:00Z
---

# Projection

Derived. Regenerated on every write. Safe to delete.

# Ledger

Append-only. Dated. Immutable. This is the truth.
```

### 4.1 The Ledger

The ledger is a dated list of events, **newest first**, matching the convention OKF uses for `log.md`. Each event is a dated heading followed by its claims. Event headings MUST use ISO 8601 `YYYY-MM-DD` form.

An event MUST NOT be edited or removed once written. A retraction is expressed by writing a new event that supersedes the earlier one. The record of having believed something is itself part of the history.

```markdown
# Ledger

## 2026-05-18 · office-hour-rota9-2026-05
- **[observed]** Cash flow in a growth cycle is now the stated bottleneck.
  → [cash-flow](/topic/cash-flow.md)
  `source: office-hour-rota9-2026-05 · writer: prof.jonathan · recorded: 2026-05-19T09:11:00Z`
- **[inferred]** May be considering raising a round. Not confirmed.
  → [fundraising](/topic/fundraising.md)
  `source: office-hour-rota9-2026-05 · writer: prof.jonathan · recorded: 2026-05-19T09:11:00Z`

## 2026-03-04 · office-hour-rota9-2026-03
- **[observed]** Structured unit economics and pricing during the session.
  → [unit-economics](/topic/unit-economics.md)
  `source: office-hour-rota9-2026-03 · writer: prof.ana · recorded: 2026-03-05T18:40:00Z`
```

### 4.2 Claims

A claim is the atomic write. It is structured on the way in, whatever it looks like on the way out.

```yaml
claim:
  subject: student/mariana-costa       # canonical id
  predicate: challenge                 # producer-defined vocabulary
  object: topic/cash-flow              # canonical id, or a literal
  tier: observed                       # REQUIRED
  source: office-hour-rota9-2026-05    # REQUIRED: a resolvable source id
  observed_at: 2026-05-18              # when it happened
  recorded_at: 2026-05-19T09:11:00Z    # when it entered the ledger
  writer: prof.jonathan@link           # who asserted it
```

A writer MUST reject a claim missing `tier`, `source`, or `writer`.

### 4.3 Tiers

Four tiers, strongest first. Producers MAY extend the list. Producers MUST NOT collapse the distinction.

| Tier | Meaning |
|---|---|
| `observed` | Said or done in a recorded, sourced interaction. |
| `public-record` | Verifiable in an external register, publication, or official site, with a URL and a fetch date. |
| `inferred` | A hypothesis by a human or a model, reasoning over other claims. |
| `self-declared` | Published by the subject about the subject. Presentation, not verification. |

Tier survives into the projection. A reader who cannot tell an interview from a guess is reading a corrupted document, however clean it looks.

### 4.4 The Projection

The projection is prose, written for a human, computed for a machine. It is regenerated in full on every write, from the full ledger, by a fixed process. It is never appended to.

Regeneration is what turns contradiction into trajectory. "Struggles with finance" from March and "commands finance" from June are not two facts fighting inside the same file. They are one arc, and a replay states it as an arc.

```markdown
# Projection

Technical founder who entered looking for management vocabulary to scale Rota9 [observed · admission interview].
Arrived skeptical of metrics-driven decision making, preferring operational intuition [observed · admission interview].
That posture changed over 2026: after structuring unit economics in a March session, she began bringing hard
numbers into subsequent sessions [observed · office hour 2026-03]. The current stated bottleneck is cash flow in a
growth cycle, no longer product [observed · office hour 2026-05]. Signals that she is weighing a raise, unconfirmed
[inferred · office hour 2026-05].

Built from 1 admission interview and 2 office hours (2025-2 through 2026-1). 3 sources. Last replay 2026-05-18.
```

Every sentence carries its tier and its source inline. An unknown field is stated as unknown rather than left blank. Degrading honestly beats degrading quietly.

---

## 5. Canon

`canon.md` sits at the bundle root as a concept of type `Canon`, which keeps it OKF conformant while giving it defined meaning under ESKF.

It maps aliases to canonical ids. The writer resolves every reference against it at write time.

```markdown
---
type: Canon
id: canon
eskf_version: "0.1"
---

# Ledger

## 2026-05-18
- **[observed]** `Finanças Corporativas`, `Finance`, `FINANÇAS` → [discipline/corporate-finance](/discipline/corporate-finance.md)
  `writer: system · confirmed_by: coord.maria@link`
```

New aliases enter as proposals and become canonical on human confirmation. A graph that fragments does so silently, and by the time anyone notices, three months of writes are pointing at the wrong node. Confirmation is cheap at write time and expensive to retrofit.

---

## 6. The Writer

A bundle has exactly one writer. It serializes writes, resolves canon, validates claims, appends to the ledger, replays the projection, and commits atomically.

Agents and humans do not write to the bundle. They propose claims to the writer.

This is the load-bearing constraint of the format. Free prose from a model, written directly into a file, is how a knowledge base rots into something that looks fine and is wrong. The writer is where format discipline lives, and it lives there so it does not have to live in the quality of whichever conversation happened to trigger the write.

A confirmation gate, when a human is in the loop, MUST display the specific claims to be written, tagged with tier and source. A generic approval button is a rubber stamp, and a rubber stamp is how garbage enters.

---

## 7. Sources and Erasure

Raw sources (transcripts, PDFs, recordings) live outside the bundle, in deletable storage, referenced from the ledger by a resolvable id.

This is a compliance property, not a storage preference. When a bundle lives in git, deleting a person from the markdown does not delete them from the history, and a deletion that leaves the data in the commit log is a deletion in name only.

Erasure under ESKF is a defined operation:

1. Delete the source artifacts from storage.
2. Remove the subject's events from every ledger that references them.
3. Replay every affected projection.

Because projections are derived and disposable, the base returns to a coherent state without the erased subject. Because the raw material never entered version control, the deletion is real.

---

## 8. Conformance

A bundle is conformant with ESKF v0.1 if:

1. It is conformant with OKF v0.1.
2. Every concept declares `id` and `eskf_version` in frontmatter.
3. Every concept that has been written to contains a `# Ledger` section.
4. Every claim in every ledger carries `tier`, `source`, and `writer`.
5. Every `# Projection` section is reproducible by replaying its ledger.
6. Every cross-reference resolves to a canonical id present in `canon.md`.

**An ESKF consumer is an OKF consumer.** It MUST tolerate unknown types, unknown fields, and broken links, per OKF §9. It SHOULD treat the ledger as authoritative and the projection as advisory whenever the two disagree.

**Any OKF consumer can read an ESKF bundle.** It will see the projection as prose and the ledger as a list. It will get less, and it will get nothing wrong.

---

## 9. Relationship to Other Work

**OKF.** ESKF is a strict superset. Same directory, same frontmatter, same links, same permissive reading. ESKF adds the event log that makes the knowledge auditable, the projection that keeps it from rotting, the claim schema that keeps inference from being laundered into fact, and the canon that keeps the graph from fragmenting.

**The LLM wiki pattern.** ESKF is that pattern with the maintenance problem taken seriously. Karpathy's original framing includes instructions for how the agent maintains the wiki. OKF kept the folder and left the maintenance out. ESKF puts it back, and specifies it.

**Event sourcing and CQRS.** The debt is obvious and acknowledged. The ledger is an event store. The projection is a materialized view. Replay is replay. What ESKF contributes is the observation that organizational memory is a write-heavy, contradiction-heavy, provenance-critical domain, which is precisely the domain event sourcing was built for, and that markdown is a perfectly good event store when the write volume is human.

**RAG.** A different problem. RAG finds a document. ESKF maintains an entity. Retrieval remains the right tool for a corpus you only ever read.

---

## 10. Versioning

This document specifies ESKF **0.1**. Minor versions add backward-compatible fields and conventions. Major versions may change required fields.

A bundle declares its target version with `eskf_version` in each concept's frontmatter.

---

## Appendix A: Minimal Bundle

```
bundle/
├── index.md
├── canon.md
├── student/
│   ├── index.md
│   └── mariana-costa.md
├── company/
│   └── rota9.md
├── discipline/
│   └── corporate-finance.md
└── topic/
    ├── cash-flow.md
    └── unit-economics.md
```

Raw sources live outside, in `sources/`, referenced by id and never committed.

---

## Appendix B: What This Costs You

Adopting ESKF costs two frontmatter fields and a writer process. If the format is abandoned tomorrow, you are left with a folder of markdown in git, which is where you were going anyway.

The format is free. The maintenance engine is the work.
