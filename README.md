# CycleRamsey

Three-colour cycle Ramsey numbers as SAT, and a measured account of how far
that gets on one desktop machine.

`R(C_a, C_b, C_c)` is the least `n` such that every red-green-blue colouring of
the edges of `K_n` contains a red `C_a`, a green `C_b` or a blue `C_c`. The
question is stated directly: colour the edges, forbid the three cycles, and ask
a solver. The formula is satisfiable exactly when `n < R`, so `R` is the least
`n` at which it is unsatisfiable.

## What is established here

**Nothing new.** Every value this repository mentions is published, and is
recorded as published rather than claimed. What it contains is a correct
encoding, an independent checker, and a measurement.

Lower bounds are re-derived from scratch and every witness is verified by
`verify_witness.py`, which reads the definition rather than the CNF and finds
cycles by its own path search, sharing no code with the encoder:

| instance | clauses | verdict | time |
|---|---:|---|---:|
| R(C_4,C_6,C_6), n=10 | 26,010 | SAT, witness verified | 0.0 s |
| R(C_6,C_6,C_6), n=11 | 83,380 | SAT, witness verified | 0.1 s |
| R(C_3,C_4,C_6), n=12 | 57,409 | SAT, witness verified | 0.1 s |
| R(C_3,C_6,C_6), n=14 | 361,088 | SAT, witness verified | 0.2 s |

Every row above is the plain encoding, no symmetry breaking, and each one has
its evidence file in `ramsey/evidence/`; the gate re-checks them all. Three of
the four also have a symmetry-broken run stored alongside, with the `_sb`
suffix and a larger clause count; `R(C_6,C_6,C_6)` at n=11 was only ever run
without the break.

The last row confirms `R(C_3,C_6,C_6) >= 15` independently.

**The upper-bound side does not finish, even for the smallest known value.**
`R(C_4,C_6,C_6) = 11` and `R(C_6,C_6,C_6) = 12` are published, so the
corresponding instances are certainly unsatisfiable; neither was decided
within the budgets tried, with or without symmetry breaking. `PREFLIGHT.md`
has the numbers and the reasoning, and says what would have to exist before
this were worth restarting.

The clause counts were never the constraint. The symmetry is.

## Layout

- `ramsey/cycles.py` — enumerate each cycle of `K_n` once. Used by the encoder
  only; the gate checks it against a closed-form count it did not come from.
- `ramsey/encode.py` — the CNF, which is the definition and nothing else. No
  symmetry breaking: a proof of a symmetry-broken formula does not prove the
  original statement.
- `ramsey/symmetry.py` — an optional, satisfiability-preserving break, with the
  argument for it and the test that checks the argument.
- `ramsey/verify_witness.py` — solver-free check of a claimed colouring, by an
  algorithm sharing nothing with the encoder.
- `ramsey/solve.py` — build, solve, verify any witness, record the evidence,
  including the solver's return code.
- `ramsey/verify_all.py` — the gate.

## Verifying

```
python ramsey/verify_all.py
```

67 checks, no solver required: the enumeration is compared against a formula,
the witness checker is made to catch a planted cycle and to miss it once an
edge is broken, every stored colouring is re-verified and then mutated
edge by edge to confirm the check can actually fail, and both the encoder and
the checker are asked for a target that is not a cycle length and must refuse.
There is no solver-backed section and no section that skips: the gate takes no
arguments, ignores any it is given, and re-checks only what is on disk. Redoing
the SAT verdicts themselves is `ramsey/solve.py`, which does need kissat and
finds it via `--kissat`, `KISSAT` or `PATH`.

## Honest limits

- No value here is a new result. The witnesses reproduce published lower
  bounds; the upper bounds were not reached.
- The measurement is of one encoding on one machine. It says that a
  symmetry-naive SAT call does not reach these upper bounds, not that they are
  unreachable — see `PREFLIGHT.md` for what would change the verdict.
