# Experimental Couples Heuristic

The package exposes an experimental couples helper at
`stable_marriage.experimental.stable_marriage_with_couples(...)`.

This module is not part of the supported root API. It is a heuristic layered
on top of Gale-Shapley-style proposals over derived receiver bases. It should
be treated as an experiment, not as a complete or formally correct solution to
the general stable matching with couples problem.

## Input Model

The helper accepts:

- `proposers`: mapping of proposer IDs to complete preference lists
- `receivers`: mapping of receiver IDs to complete preference lists
- `couples`: mapping of couple IDs to the ordered member IDs belonging to that
  couple

The base one-to-one validation still applies:

- every proposer must rank every receiver exactly once
- every receiver must rank every proposer exactly once
- the number of proposers must equal the number of receivers

Additional couples constraints:

- each couple member must appear in `proposers`
- a proposer may appear in at most one couple
- couple members must collapse to the same ordered sequence of receiver bases
- every preferred base must contain enough distinct receiver slots for the full
  couple

## Receiver Base Model

The heuristic does not use structured hospital or slot objects. Instead, it
derives a base identifier from the receiver label by stripping the trailing slot
suffix.

Examples:

- `H1_A` becomes base `H1`
- `Hospital-1-SlotA` becomes base `Hospital-1`

Couple placement is driven by these derived bases rather than by explicit
metadata.

## Guarantees When It Returns

If `stable_marriage_with_couples(...)` returns successfully, the result
satisfies these properties:

- every proposer is assigned to exactly one receiver
- no receiver is assigned to more than one proposer
- members of the same couple are assigned to distinct receivers with the same
  derived base

These are the guarantees of the current heuristic. They are not equivalent to a
general proof of stability for the stable matching with couples problem.

## Non-Guarantees

This helper does not guarantee:

- a stable matching in the general couples sense
- completeness for all valid instances
- that a raised `ValueError` means no acceptable assignment exists
- compatibility with a CLI JSON schema, because the installed CLI does not
  support couples input

## Known Failure Modes

- The heuristic can reject an instance even when a valid assignment may exist.
- Couple members with different collapsed base orders are rejected during
  validation.
- Bases with too few distinct receiver slots for the couple size are rejected
  during validation.
- The base-derivation rule depends on receiver naming conventions such as
  `_SlotA` or `-SlotA`.

## Recommendation

Use the root `stable_marriage(...)` API for supported one-to-one matching.

Use `stable_marriage.experimental.stable_marriage_with_couples(...)` only when
you explicitly accept heuristic behavior and its limitations.
