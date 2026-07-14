# ESKF

**Event-Sourced Knowledge Format.** Organizational memory for AI agents that stays correct over time.

A knowledge base for agents is easy to build and hard to keep true. The failure never shows up in week one. It shows up in month six, when the base has absorbed a few hundred writes from a dozen sources, half of them inferences, and nobody can tell which sentence came from a recorded interview and which one came from a model guessing on a Tuesday.

ESKF is [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) plus the maintenance engine OKF leaves to the producer. Any OKF consumer can read an ESKF bundle without modification.

**[Read the spec](SPEC.md)** (one page) · **[See a bundle](examples/minimal-bundle/)** · **[Validate yours](tools/eskf-lint/)**

---

## The six laws

| # | Law | Failure it prevents |
|---|---|---|
| **L1** | The ledger is append-only, dated, and immutable. | Loss of history |
| **L2** | The projection is regenerated from the full ledger and never appended to. | Rot |
| **L3** | Every claim carries provenance and an epistemic tier. | Laundering inference into fact |
| **L4** | Writes go through a single writer and accept structured claims only. | Drift |
| **L5** | Every reference resolves to a canonical id. | Silent graph fragmentation |
| **L6** | The output remains OKF conformant. | Lock-in |

The whole format is those six sentences. Everything in the spec is the mechanics of enforcing them.

## What a concept looks like

```markdown
---
type: Student
id: student/mariana-costa
eskf_version: "0.1"
projection_of: 3          # events replayed into the projection below
projected_at: 2026-05-19T09:11:00Z
---

# Projection

Technical founder who joined looking for management vocabulary to scale Rota9
[observed · admission interview 2026-02]. Arrived skeptical of metrics-driven decision
making [self-declared · admission interview 2026-02]. That posture moved: by May the
stated bottleneck had shifted from product to cash flow [observed · office hour 2026-05].
She may be preparing to raise, unconfirmed [inferred · office hour 2026-05].

# Ledger

## 2026-05-18 · office-hour-2026-05
- **[observed]** Cash flow in a growth cycle is now the stated bottleneck.
  → [cash-flow](/topic/cash-flow.md)
  `source: office-hour-2026-05 · writer: prof.jonathan@example.edu · recorded: 2026-05-19T09:11:00Z`
- **[inferred]** May be preparing to raise. Mentioned runway twice unprompted.
  → [fundraising](/topic/fundraising.md)
  `source: office-hour-2026-05 · writer: prof.jonathan@example.edu · recorded: 2026-05-19T09:11:00Z`
```

Two sections. The **ledger** is the truth: append-only, dated, immutable. The **projection** is derived, regenerated on every write from the whole ledger, and safe to delete.

That distinction is the entire idea. Regeneration is what turns contradiction into trajectory: "struggles with finance" in March and "commands finance" in June stop being two facts fighting inside one file, and become one arc that a replay can state as an arc.

The tier tags are the other half. A reader who cannot tell an interview from a guess is reading a corrupted document, however clean it looks.

## Validate a bundle

```bash
python3 tools/eskf-lint/eskf_lint.py examples/minimal-bundle
```

```
7 concepts, 10 events, 13 claims
CONFORMANT with ESKF v0.1
```

Zero dependencies, standard library only. It checks all six laws, including the one that matters most in practice: whether your projection is stale relative to its ledger.

## Why not RAG

RAG rediscovers knowledge from scratch on every query. Nothing accumulates. Ask a question that needs five documents synthesized, and the model does that synthesis again, and again, and again, and reaches a slightly different conclusion each time.

The LLM-wiki pattern, [described by Andrej Karpathy in April 2026](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), inverts this: an agent reads each new source once and integrates it into a persistent, interlinked markdown base. Google Cloud formalized the artifact as OKF in June 2026.

ESKF is about what happens next, at month six. OKF has a `timestamp` field, and a field is not a process. ESKF specifies the process.

## Relationship to OKF

An ESKF bundle **is** an OKF bundle. Same directory, same YAML frontmatter, same markdown links, same permissive reading rules. Point any OKF consumer at it and it works: it will see the projection as prose and the ledger as a list. It will get less, and it will get nothing wrong.

What ESKF adds is exactly what OKF declares out of scope:

| OKF leaves to the producer | ESKF specifies |
|---|---|
| How knowledge is maintained | Replay: the projection is a pure function of the ledger |
| How agents write without making a mess | A single writer that accepts structured claims only |
| What `type` values mean | A canon of ids and aliases, resolved at write time |
| Where a claim came from | Provenance and tier on every claim, preserved into the projection |

## Status

**v0.1, draft.** Written because we needed it in production, published because the problem is not ours alone. The spec is stable enough to build on and young enough to argue with. Issues and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

No SLA on response time. The spec is maintained as it evolves in production use.

## What this costs you

Two frontmatter fields and a writer process. If the format is abandoned tomorrow, you are left with a folder of markdown in git, which is where you were going anyway.

The format is free. The maintenance engine is the work.

## License

Apache 2.0. See [LICENSE](LICENSE).
