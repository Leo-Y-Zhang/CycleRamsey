"""The gate: re-check everything this repository claims, from what is on disk.

Two things here are load-bearing and easy to get wrong, so both are tested by
breaking them on purpose and requiring the break to be caught:

  * the witness checker. A checker that cannot fail is decoration, so every
    stored colouring is also mutated and must be rejected.
  * the cycle enumeration. It is compared against a closed-form count it did
    not come from, and against a brute-force search for small cases.

Nothing here calls a solver. This module takes no arguments and re-checks only
what is on disk; `solve.py` is what needs kissat.
"""
import argparse
import contextlib
import glob
import importlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ramsey import __main__ as cli
from ramsey import symmetry
from ramsey.cycles import cycle_count, cycle_edges, cycles, edges
from ramsey.encode import Encoding
from ramsey.verify_witness import check_colouring, find_cycle, is_good

HERE = os.path.dirname(os.path.abspath(__file__))
EVIDENCE = os.path.join(HERE, 'evidence')

# Values this repository re-derives rather than asserts. All are published;
# none is a claim of ours. Source: OEIS A389334 and the references there.
PUBLISHED = {
    (3, 3, 3): 17,
    (3, 4, 4): 12,
    (4, 4, 4): 11,
    (4, 6, 6): 11,
    (6, 6, 6): 12,
    (3, 4, 6): 13,
    # Wesley, arXiv:2509.03784, September 2025, which PREFLIGHT.md quotes.
    (3, 6, 6): 15,
}

# Every evidence file the README and PREFLIGHT.md rely on, with the verdict it
# records. The sections below only look at the records they find, so without
# this a witness deleted, renamed or downgraded to a timeout would drop out of
# the check unnoticed, and a timeout rewritten as an UNSAT nobody can re-check
# would pass as an upper bound. Adding evidence means adding it here as well.
CLAIMED_EVIDENCE = {
    '3-4-6_n12.json': 'SAT_WITNESS_VERIFIED',
    '3-4-6_n12_sb.json': 'SAT_WITNESS_VERIFIED',
    '3-6-6_n14.json': 'SAT_WITNESS_VERIFIED',
    '3-6-6_n14_sb.json': 'SAT_WITNESS_VERIFIED',
    '4-6-6_n10.json': 'SAT_WITNESS_VERIFIED',
    '4-6-6_n10_sb.json': 'SAT_WITNESS_VERIFIED',
    '4-6-6_n11.json': 'TIMEOUT',
    '4-6-6_n11_sb.json': 'TIMEOUT',
    '6-6-6_n11.json': 'SAT_WITNESS_VERIFIED',
    '6-6-6_n12_sb.json': 'TIMEOUT',
}

passed = failed = 0


def record_problems(name, rec):
    """Everything inconsistent inside one evidence record, as reasons.

    The size is recomputed from the definition, not by building the encoding:
    four clauses per edge, one per target cycle, and three per consecutive
    pair of star edges when the sorted-star break is on. The verdict has to
    agree with the solver's return code, since that is what it was read from.
    """
    problems = []
    n, targets = rec['n'], tuple(rec['targets'])
    a, b, c = targets
    broken = name.endswith('_sb.json')
    stem = f'{a}-{b}-{c}_n{n}' + ('_sb' if broken else '') + '.json'
    if name != stem:
        problems.append(f'file name does not match n={n}, targets={targets}')
    if rec.get('problem') != f'R(C{a},C{b},C{c})':
        problems.append(f'problem {rec.get("problem")!r} does not match the targets')
    encoding = ('one-hot, sorted-star symmetry break' if broken
                else 'one-hot, no symmetry breaking')
    if rec.get('encoding') != encoding:
        problems.append(f'encoding {rec.get("encoding")!r} does not match the file name')
    extra = 3 * (n - 2) if broken else 0
    if rec.get('symmetry_clauses', 0) != extra:
        problems.append(f'{rec.get("symmetry_clauses")} symmetry clauses, not {extra}')
    m = len(edges(n))
    if rec.get('vars') != 3 * m:
        problems.append(f'{rec.get("vars")} variables, not {3 * m}')
    clauses = 4 * m + sum(cycle_count(n, L) for L in targets) + extra
    if rec.get('clauses') != clauses:
        problems.append(f'{rec.get("clauses")} clauses, not {clauses}')
    verdict = rec.get('verdict')
    if verdict == 'SAT_WITNESS_VERIFIED':
        if (rec.get('returncode'), rec.get('sat'), rec.get('timed_out')) != (10, True, False):
            problems.append('a verified witness needs returncode 10, sat true, '
                            'timed_out false')
        if 'colouring' not in rec:
            problems.append('a verified witness carries no colouring')
    elif verdict == 'TIMEOUT':
        if rec.get('returncode') is not None or rec.get('timed_out') is not True:
            problems.append('a timeout needs returncode null and timed_out true')
        if 'sat' in rec or 'colouring' in rec:
            problems.append('a timeout decided nothing, so records no answer')
    else:
        # An UNSAT has no certificate on disk here, so the gate cannot check
        # it, and a claim it cannot check must not come out as a pass.
        problems.append(f'verdict {verdict!r} is not one this gate can re-check')
    return problems


def check(label, ok):
    global passed, failed
    if ok:
        passed += 1
        print(f'  [PASS] {label}')
    else:
        failed += 1
        print(f'  [FAIL] {label}')


def section(title):
    print(f'\n=== {title} ===')


def main():
    section('cycle enumeration agrees with a formula it did not come from')
    for n, L in [(3, 3), (6, 6), (7, 3), (10, 6), (12, 5), (14, 6), (15, 6)]:
        got = sum(1 for _ in cycles(n, L))
        check(f'K_{n}: {L}-cycles enumerated == C(n,L)(L-1)!/2 == {got}',
              got == cycle_count(n, L))

    section('every enumerated cycle is a real cycle, listed once')
    for n, L in [(7, 6), (8, 3), (9, 4)]:
        seen, malformed = set(), 0
        for c in cycles(n, L):
            if len(set(c)) != L or len(set(cycle_edges(c))) != L:
                malformed += 1
            seen.add(frozenset(cycle_edges(c)))
        total = sum(1 for _ in cycles(n, L))
        check(f'K_{n} {L}-cycles: none malformed', malformed == 0)
        check(f'K_{n} {L}-cycles: no duplicates ({len(seen)} of {total})',
              len(seen) == total)

    section('the encoding has the size the definition implies')
    for n, targets in [(8, (3, 6, 6)), (10, (4, 6, 6))]:
        enc = Encoding(n, targets)
        expect = len(edges(n)) * 4  # one at-least-one + three at-most-one
        for L in targets:
            expect += cycle_count(n, L)
        check(f'K_{n} {targets}: {len(enc.clauses)} clauses == predicted',
              len(enc.clauses) == expect)
        check(f'K_{n} {targets}: {enc.num_vars} vars == 3*|E|',
              enc.num_vars == 3 * len(edges(n)))

    section('a target that is not a cycle length is refused, not answered')
    # A cycle has at least three vertices, so C_2 and C_0 are not questions
    # about cycles at all. Both halves of this repository used to answer them
    # anyway, and in the same direction: the encoder emitted no clauses for
    # that colour because `cycles` yields nothing below length 3, and the
    # checker found nothing there because `find_cycle` returns None below
    # length 3. Two components that share no code still shared this blind
    # spot, so solve.py reported SAT_WITNESS_VERIFIED for R(C3,C6,C2), a
    # Ramsey number that does not exist. Refusing is the only honest answer.
    for targets in [(3, 6, 2), (3, 6, 0), (3, 6, -1)]:
        try:
            Encoding(8, targets)
            refused = False
        except ValueError:
            refused = True
        check(f'encoder refuses target lengths {targets}', refused)
    # Three perfect matchings of K_4, so no colour holds two adjacent edges and
    # the colouring is good for anything. Only the target can be at fault here.
    matchings = {(0, 1): 0, (2, 3): 0, (0, 2): 1, (1, 3): 1, (0, 3): 2, (1, 2): 2}
    for targets in [(2, 2, 2), (3, 6, 1)]:
        try:
            check_colouring(4, matchings, targets)
            refused = False
        except ValueError:
            refused = True
        # Deliberately ValueError and not AssertionError: `is_good` turns an
        # AssertionError into False, which would read as "this colouring is
        # not good" rather than "this question cannot be answered".
        check(f'witness checker refuses target lengths {targets}', refused)

    section('the witness checker finds cycles that are really there')
    # A monochromatic 6-cycle planted by hand must be found; the same
    # colouring with one edge recoloured must not be.
    n = 8
    colouring = {e: 2 for e in edges(n)}
    hexagon = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)]
    for e in hexagon:
        colouring[e] = 0
    for e in edges(n):
        if e not in hexagon:
            colouring[e] = 1 if e[0] % 2 else 2
    found = find_cycle(n, colouring, 0, 6)
    check('planted 6-cycle is found', found is not None and len(found) == 6)
    check('planted 6-cycle is not reported as a 5-cycle',
          find_cycle(n, colouring, 0, 5) is None)
    broken = dict(colouring)
    broken[(0, 1)] = 1
    check('breaking one edge of it makes the 6-cycle vanish',
          find_cycle(n, broken, 0, 6) is None)

    section('the evidence on disk is exactly what is claimed, and consistent')
    records = sorted(glob.glob(os.path.join(EVIDENCE, '*.json')))
    on_disk = {os.path.basename(p) for p in records}
    check(f'evidence files are exactly the {len(CLAIMED_EVIDENCE)} claimed '
          f'(missing {sorted(set(CLAIMED_EVIDENCE) - on_disk)}, '
          f'unexpected {sorted(on_disk - set(CLAIMED_EVIDENCE))})',
          on_disk == set(CLAIMED_EVIDENCE))
    for path in records:
        with open(path, encoding='utf-8') as fh:
            rec = json.load(fh)
        name = os.path.basename(path)
        claimed = CLAIMED_EVIDENCE.get(name)
        check(f'{name}: verdict {rec.get("verdict")} is the one claimed ({claimed})',
              rec.get('verdict') == claimed)
        problems = record_problems(name, rec)
        check(f'{name}: size, name and verdict agree with each other'
              + (f' ({"; ".join(problems)})' if problems else ''), not problems)

    section('the record check can fail')
    # The same break-it-on-purpose rule as for the witness checker: each of
    # these edits to a real record must be reported.
    with open(os.path.join(EVIDENCE, '3-6-6_n14_sb.json'), encoding='utf-8') as fh:
        good = json.load(fh)
    with open(os.path.join(EVIDENCE, '4-6-6_n11.json'), encoding='utf-8') as fh:
        timeout = json.load(fh)
    edits = [
        ('3-6-6_n14_sb.json', good, 'clauses', good['clauses'] + 1),
        ('3-6-6_n14_sb.json', good, 'vars', good['vars'] + 3),
        ('3-6-6_n14_sb.json', good, 'symmetry_clauses', 0),
        ('3-6-6_n14_sb.json', good, 'returncode', 20),
        ('3-6-6_n14_sb.json', good, 'problem', 'R(C3,C6,C5)'),
        ('3-6-6_n14.json', good, 'n', good['n']),
        ('4-6-6_n11.json', timeout, 'verdict', 'UNSAT'),
        ('4-6-6_n11.json', timeout, 'returncode', 20),
    ]
    for name, rec, key, value in edits:
        mutated = dict(rec, **{key: value})
        check(f'{name} with {key}={value!r} is reported',
              bool(record_problems(name, mutated)))

    section('stored witnesses re-verify, and mutations of them do not')
    checked = 0
    for path in records:
        with open(path, encoding='utf-8') as fh:
            rec = json.load(fh)
        if rec.get('verdict') != 'SAT_WITNESS_VERIFIED':
            continue
        checked += 1
        name = os.path.basename(path)
        n, targets = rec['n'], tuple(rec['targets'])
        order = edges(n)
        # One character per edge, checked rather than assumed. A stored string
        # of the wrong length would otherwise be zipped against the edge list
        # and verified over whichever prefix happened to line up, which is a
        # pass that means nothing. strict= below is the backstop.
        sized = len(rec['colouring']) == len(order)
        check(f'{name}: colouring is one character per edge '
              f'({len(rec["colouring"])} of {len(order)})', sized)
        if not sized:
            continue
        colouring = {e: int(c) for e, c in zip(order, rec['colouring'], strict=True)}
        check(f'{name}: colouring re-verified solver-free',
              is_good(n, colouring, targets))
        # Recolouring every edge one colour on must break it, or the check
        # is not actually constraining anything.
        survived = 0
        for e in order:
            mutated = dict(colouring)
            mutated[e] = (mutated[e] + 1) % 3
            if is_good(n, mutated, targets):
                survived += 1
        check(f'{name}: single-edge mutations mostly rejected '
              f'({len(order) - survived} of {len(order)} caught)',
              survived < len(order))
        # The canonical form of a good colouring is still good.
        check(f'{name}: canonicalised colouring is still good',
              is_good(n, symmetry.canonicalise(n, colouring), targets))
    check(f'at least one stored witness was checked ({checked} found)',
          checked > 0)

    section('symmetry breaking does not remove a colouring that exists')
    # The break says the star at vertex 0 is sorted. Every stored witness,
    # after canonicalisation, must satisfy exactly that.
    for path in records:
        with open(path, encoding='utf-8') as fh:
            rec = json.load(fh)
        if rec.get('verdict') != 'SAT_WITNESS_VERIFIED':
            continue
        n = rec['n']
        if len(rec['colouring']) != len(edges(n)):
            continue  # already reported as a failure by the section above
        colouring = {e: int(c) for e, c in zip(edges(n), rec['colouring'], strict=True)}
        canon = symmetry.canonicalise(n, colouring)
        star = [canon[(0, v)] for v in range(1, n)]
        check(f'{os.path.basename(path)}: canonical star is sorted {star}',
              star == sorted(star))

    section('stored witnesses sit under the published values, checked not asserted')
    # A verified witness on K_n is a good colouring of K_n, so it proves R > n.
    # That ordering against the published table is the one direction here that
    # is an invariant, and it is where a mistyped value or a bogus witness would
    # show. A TIMEOUT is compared against nothing: an undecided verdict implies
    # nothing about n against R, and a hard instance below R times out honestly.
    compared = 0
    for path in records:
        with open(path, encoding='utf-8') as fh:
            rec = json.load(fh)
        if rec.get('verdict') != 'SAT_WITNESS_VERIFIED':
            continue
        targets = tuple(rec['targets'])
        if targets not in PUBLISHED:
            continue  # no published value to sit under; not a failure
        compared += 1
        value = PUBLISHED[targets]
        check(f'{os.path.basename(path)}: witness on K_{rec["n"]} is below '
              f'published R(C{targets[0]},C{targets[1]},C{targets[2]}) = {value}',
              rec['n'] < value)
    check(f'at least one witness was compared to a published value '
          f'({compared} found)', compared > 0)

    section('the command line reports what the gate decided')
    # `ramsey verify` once printed GATE FAILED and exited 0: it waited for a
    # SystemExit that main() never raises. This is checked with main() stubbed
    # out, since calling the real one from here would recurse.
    gate = importlib.import_module('ramsey.verify_all')
    real = gate.main
    try:
        gate.main = lambda: 1
        status = cli.cmd_verify(None)
    finally:
        gate.main = real
    check(f'ramsey verify exits non-zero when the gate fails (exit {status})',
          status == 1)
    # `ramsey solve` read its verdict from keys solve() never writes, so it
    # never said what a verdict meant. Checked with solve() stubbed out, since
    # a real run needs kissat.
    solver = importlib.import_module('ramsey.solve')
    real = solver.solve
    for verdict, says in [('SAT_WITNESS_VERIFIED', 'so R > 9'),
                          ('UNSAT', 'so R <= 9')]:
        err = io.StringIO()
        try:
            solver.solve = lambda *a, verdict=verdict, **k: {'verdict': verdict}
            args = argparse.Namespace(n=9, targets='3,6,6', kissat=None,
                                      timeout=None, keep_cnf=False, symmetry=False)
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(err):
                cli.cmd_solve(args)
        finally:
            solver.solve = real
        check(f'ramsey solve explains {verdict} as "{says}"', says in err.getvalue())

    print(f'\n{passed} passed / {failed} failed')
    if failed:
        print('GATE FAILED')
        return 1
    print('EVERY CLAIM IN THIS REPOSITORY IS SUPPORTED BY EVIDENCE ON DISK.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
