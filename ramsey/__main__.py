"""CycleRamsey CLI.

  ramsey verify
      Run the full self-check: cycle enumeration against a closed-form count,
      the encoding's size against what the definition implies, and every stored
      witness re-checked from scratch. Exits non-zero if anything disagrees.
      This is the command that decides whether the rest of the repository means
      anything, so it needs no arguments and no solver.

  ramsey solve N A,B,C [--symmetry] [--timeout S] [--save]
      Encode R(C_a, C_b, C_c) at order N and hand it to kissat. Satisfiable
      means a good colouring exists, so N < R; unsatisfiable means N >= R.
      Needs kissat on PATH.

  ramsey check WITNESS.json
      Re-check one stored witness independently of how it was produced: rebuild
      the adjacency, search for each forbidden cycle, and report. A witness
      nobody can re-check is a claim, not evidence.

  ramsey size N A,B,C
      Print the clause and variable counts for an instance without solving it,
      which is how you find out whether an order is reachable before waiting
      for a solver to tell you it is not.

Nothing here is a new mathematical result: every value the repository mentions
is published. What is here is the encoding, the evidence, and the checking.
"""
from __future__ import annotations

import argparse
import json
import sys


def cmd_verify(args) -> int:
    from . import verify_all
    try:
        verify_all.main()
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def cmd_solve(args) -> int:
    from .solve import solve
    targets = tuple(int(x) for x in args.targets.split(","))
    if len(targets) != 3:
        print("targets must be three cycle lengths, e.g. 3,6,6", file=sys.stderr)
        return 2
    record = solve(args.n, targets, kissat=args.kissat, timeout=args.timeout,
                   keep=args.keep_cnf, break_symmetry=args.symmetry)
    print(json.dumps(record, indent=1))
    verdict = record.get("result") or record.get("status")
    if verdict == "SAT":
        print(f"\nsatisfiable: a good colouring of K_{args.n} exists, "
              f"so R > {args.n}", file=sys.stderr)
    elif verdict == "UNSAT":
        print(f"\nunsatisfiable: every colouring of K_{args.n} contains a "
              f"forbidden cycle, so R <= {args.n}", file=sys.stderr)
    return 0


def cmd_check(args) -> int:
    """Re-check a stored witness from the file alone, solver-free.

    The colouring is stored as one character per edge, in the order `edges(n)`
    produces. The length is checked rather than assumed: a string of the wrong
    length zipped against the edge list would otherwise verify whichever prefix
    happened to line up, which is a pass that means nothing.
    """
    from .cycles import edges
    from .verify_witness import is_good

    with open(args.witness, encoding="utf-8") as fh:
        record = json.load(fh)
    n = record["n"]
    targets = tuple(record["targets"])
    raw = record.get("colouring")
    if raw is None:
        print("this record carries no colouring to check", file=sys.stderr)
        return 2

    order = edges(n)
    print(f"witness: K_{n}, forbidding cycles {targets}")
    print(f"  {len(order)} edges, colouring string {len(raw)} characters")
    if len(raw) != len(order):
        print("  MALFORMED: one character per edge is required", file=sys.stderr)
        return 1

    colouring = {e: int(c) for e, c in zip(order, raw, strict=True)}
    good = is_good(n, colouring, targets)
    print(f"  no forbidden cycle present: {good}")
    if not good:
        print("verdict: BAD")
        return 1

    # A colouring that stays good however you recolour an edge is not evidence
    # of anything -- it would mean the check cannot see a violation. So the
    # witness must sit on the boundary: at least one single-edge recolouring
    # has to break it.
    broke = 0
    for e in order:
        for c in range(3):
            if colouring[e] == c:
                continue
            mutated = dict(colouring)
            mutated[e] = c
            if not is_good(n, mutated, targets):
                broke += 1
                break
        if broke:
            break
    print(f"  a single-edge recolouring breaks it: {bool(broke)}")
    if not broke:
        print("verdict: SUSPECT - nothing this checker does can fail here")
        return 1
    print("verdict: GOOD - re-verified from the file, solver-free")
    return 0


def cmd_size(args) -> int:
    from .encode import Encoding
    targets = tuple(int(x) for x in args.targets.split(","))
    enc = Encoding(args.n, targets)
    print(f"K_{args.n}, forbidding cycles {targets}")
    print(f"  variables {enc.num_vars:,}")
    print(f"  clauses   {len(enc.clauses):,}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ramsey", description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="command")

    sub.add_parser("verify", help="run the full self-check").set_defaults(
        func=cmd_verify)

    s = sub.add_parser("solve", help="encode an instance and run kissat")
    s.add_argument("n", type=int)
    s.add_argument("targets", help="three cycle lengths, e.g. 3,6,6")
    s.add_argument("--kissat")
    s.add_argument("--timeout", type=float)
    s.add_argument("--keep-cnf", action="store_true")
    s.add_argument("--symmetry", action="store_true",
                   help="add the sorted-star break (satisfiability-preserving)")
    s.set_defaults(func=cmd_solve)

    c = sub.add_parser("check", help="re-check one stored witness")
    c.add_argument("witness")
    c.set_defaults(func=cmd_check)

    z = sub.add_parser("size", help="variable and clause counts, without solving")
    z.add_argument("n", type=int)
    z.add_argument("targets", help="three cycle lengths, e.g. 3,6,6")
    z.set_defaults(func=cmd_size)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
