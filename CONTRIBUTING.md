# Contributing to ESKF

The format is small on purpose. The bar for adding to it is high, and the bar for
questioning it is low. Both of those are intentional.

## What is most useful

**Tell us where it broke.** A bundle that hit a wall in production is worth more than a
proposal. Open an issue with the shape of the knowledge you were modeling and the point
at which the six laws stopped helping.

**Consumers and producers.** The format matters only if things read and write it. A tool
that emits conformant bundles, or an agent that consumes them, does more for the spec
than any amount of prose.

**Attacks on the laws.** If one of the six is wrong, say so with a case. The laws earn
their place by preventing a specific failure, and a law that prevents nothing should go.

## Proposing a change to the spec

Open an issue before a PR. The questions any proposal has to answer:

1. What failure does this prevent? Name it concretely.
2. Does it break OKF conformance? If yes, it will not land (L6).
3. Can a producer already do this with `# Citations`, a custom frontmatter key, or a new
   `type` value? If yes, it belongs in the producer, not the spec.
4. Does it make the format bigger? Every addition is a tax on everyone who implements it.

Additions that are optional, backward compatible, and clearly motivated have a good path.
Additions that make ESKF a platform rather than a format do not.

## The linter

`tools/eskf-lint/` is standard library only, Python 3.8+, and stays that way. A validator
that needs a dependency tree is a validator people skip.

Every new check needs a test case in `examples/`, a stable error code, and a message that
names the law it enforces.

## Conventions

- Prose in the spec is normative when it says MUST, SHOULD, or MAY. Everything else is
  explanation, and explanation should be short.
- Examples use `example.edu` and `example.com`. No real people, ever, in a spec about
  provenance of claims about real people.
- Commits: imperative mood, one concern each.

## Governance

Small and informal for now. Maintainers merge, decisions get argued in the open, and if
this ever grows past what that supports, we will say so here.

## License

Contributions are accepted under Apache 2.0, the license of this repository.
