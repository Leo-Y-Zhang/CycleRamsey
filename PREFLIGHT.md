# Pre-flight for R(C_3, C_6, C_6) — and why it stopped here

This repository was started to compute the first unknown value of OEIS
[A389334](https://oeis.org/A389334), the three-colour cycle Ramsey numbers.
The entry's own comment says:

> The first unknown value is 15 <= T(3,6,6) <= 18.

Two things came out of the pre-flight, in this order. Both are reasons not to
carry on, and both are recorded because a measurement that stops a project is
worth as much as one that starts it.

## 1. The value is not unknown. It was published in September 2025

William J. Wesley, *New bounds for some small multicolor Ramsey numbers*,
[arXiv:2509.03784](https://arxiv.org/abs/2509.03784), 4 September 2025:

> we tighten some recent upper bounds for multicolor Ramsey numbers for cycles
> and show R(C_3,C_6,C_6) = R(C_5,C_6,C_6) = 15.

That is five months before A389334 was created (Elijah Beregovsky, 30 September
2025), so the entry is simply behind the literature rather than describing an
open problem. The paper is a preprint — "comments welcome", no journal
reference — which is what made independent verification look worth doing.

## 2. Independent verification is out of reach on this machine

The question is stated directly as SAT. Colour the edges of K_n in three
colours; forbid a C_3 in colour 0 and a C_6 in colours 1 and 2. The formula is
satisfiable exactly when n < R, so R is the least n at which it is
unsatisfiable. The encoding is the definition, with no symmetry breaking, and
any satisfying assignment is checked by `verify_witness.py`, which reads the
definition rather than the CNF and finds cycles by its own path search.

**The satisfiable side is trivial.** Every lower bound tested was decided in
under a second and every witness verified:

| instance | clauses | verdict | time |
|---|---:|---|---:|
| R(C_4,C_6,C_6), n=10 | 26,010 | SAT, witness verified | 0.0 s |
| R(C_6,C_6,C_6), n=11 | 83,380 | SAT, witness verified | 0.1 s |
| R(C_3,C_4,C_6), n=12 | 57,409 | SAT, witness verified | 0.1 s |
| **R(C_3,C_6,C_6), n=14** | **361,088** | **SAT, witness verified** | **0.2 s** |

All four are the plain encoding with no symmetry breaking, and all four are
stored in `ramsey/evidence/`.

The last row is an independent confirmation that **R(C_3,C_6,C_6) >= 15**. It
is also the half that was already known before Wesley: the lower bound 15 is
in the OEIS comment. Confirming it adds nothing to the literature.

**The unsatisfiable side does not finish, even for the smallest known value.**

| instance | clauses | symmetry break | result |
|---|---:|---|---|
| R(C_4,C_6,C_6), n=11 | 56,650 | none | no verdict in 45 min |
| R(C_4,C_6,C_6), n=11 | 56,677 | sorted star | no verdict in 500 s |
| R(C_6,C_6,C_6), n=12 | 166,614 | sorted star | no verdict in 400 s |

Both of those are **published values** — R(C_4,C_6,C_6) = 11 and
R(C_6,C_6,C_6) = 12 — so both instances are certainly unsatisfiable. The
solver cannot show it. These are the two smallest upper bounds in the whole
C_6 family, on formulas of well under 200,000 clauses; the target instance is
K_15 with 600,600 six-cycle clauses and a vertex group of 15! rather than 11!.

The clause count was never the constraint. The symmetry is. A monolithic SAT
call over K_n carries the full S_n action plus the colour swap, and the
sorted-star break removes only the ordering of one vertex's incident edges —
measured above as no help at all.

## Verdict: NO-GO, and what would change it

Not "this is hard". Specifically: **the upper-bound side of three-colour cycle
Ramsey numbers is not reachable by a single symmetry-naive SAT call**, and
nothing short of isomorphism-free search will change that. In rough order of
what would have to exist first:

1. **SAT modulo symmetries** (Kirchweger and Szeider) or equivalent canonical
   augmentation, so isomorphic colourings are never explored twice. This is
   what modern Ramsey computations actually use, and it is a different program
   from the one here, not a flag on it.
2. Failing that, **cube-and-conquer over the colour degree sequence at a
   vertex**, which at least splits the space along an invariant.
3. Only then is a K_15 refutation worth attempting, and it would still be
   reproducing a published result.

Until (1) exists, this is a no-go. The repository is kept because the
satisfiable side, the witness checker and the gate are correct and reusable,
and because the measurement above is the evidence for the decision.

## What is here

Nothing in this repository is a new mathematical claim. The values in
`verify_all.py` are published and are recorded as such; the only things
computed here are witnesses that reproduce known lower bounds, and the
timings above.
