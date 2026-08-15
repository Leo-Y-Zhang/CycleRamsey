"""Build an instance, solve it, check any witness, and write the evidence.

Every run records kissat's return code. An earlier project of mine lost a day
to a solver that died silently with empty output, because the evidence file
could not tell a crash from a refusal. One unexplained failure is not a
ceiling; it is a missing measurement.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ramsey import symmetry
from ramsey.encode import Encoding
from ramsey.verify_witness import check_colouring

HERE = os.path.dirname(os.path.abspath(__file__))
EVIDENCE = os.path.join(HERE, 'evidence')

SAT, UNSAT = 10, 20


def find_kissat(explicit=None):
    path = explicit or os.environ.get('KISSAT') or shutil.which('kissat')
    if path and os.path.exists(path):
        return path
    if path and shutil.which(path):
        return shutil.which(path)
    return None


def run_kissat(kissat, cnf, timeout=None, proof=None):
    cmd = [kissat, '-q', cnf]
    if proof:
        cmd = [kissat, '-q', '--no-binary', cnf, proof]
    started = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'returncode': None, 'timeout': True,
                'seconds': round(time.time() - started, 1),
                'stdout': '', 'stderr': ''}
    return {'returncode': proc.returncode, 'timeout': False,
            'seconds': round(time.time() - started, 1),
            'stdout': proc.stdout, 'stderr': proc.stderr}


def parse_model(stdout):
    lits = []
    for line in stdout.splitlines():
        if line.startswith('v '):
            lits.extend(int(t) for t in line[2:].split())
    return [x for x in lits if x != 0]


def solve(n, targets, kissat=None, timeout=None, workdir=None, keep=False,
          break_symmetry=False):
    """Decide K_n for `targets`, verifying any witness before reporting it."""
    kissat_path = find_kissat(kissat)
    if kissat_path is None:
        raise SystemExit('kissat not found: pass --kissat or set KISSAT')

    workdir = workdir or EVIDENCE
    os.makedirs(workdir, exist_ok=True)
    tag = f'n{n}_c{targets[0]}-{targets[1]}-{targets[2]}'
    cnf = os.path.join(workdir, tag + '.cnf')

    build_started = time.time()
    enc = Encoding(n, targets)
    sb_clauses = symmetry.apply(enc) if break_symmetry else 0
    enc.to_dimacs(cnf)
    build_s = round(time.time() - build_started, 1)

    result = run_kissat(kissat_path, cnf, timeout=timeout)

    record = {
        'problem': f'R(C{targets[0]},C{targets[1]},C{targets[2]})',
        'n': n,
        'targets': list(targets),
        'vars': enc.num_vars,
        'clauses': len(enc.clauses),
        'build_s': build_s,
        'solve_s': result['seconds'],
        'returncode': result['returncode'],
        'timed_out': result['timeout'],
        'encoding': ('one-hot, sorted-star symmetry break' if break_symmetry
                     else 'one-hot, no symmetry breaking'),
        'symmetry_clauses': sb_clauses,
    }

    if result['timeout']:
        record['verdict'] = 'TIMEOUT'
    elif result['returncode'] == UNSAT:
        record['sat'] = False
        record['verdict'] = 'UNSAT'
    elif result['returncode'] == SAT:
        record['sat'] = True
        colouring = enc.colouring_from_model(parse_model(result['stdout']))
        # The witness is checked by code that never saw the CNF.
        check_colouring(n, colouring, targets)
        record['verdict'] = 'SAT_WITNESS_VERIFIED'
        record['colouring'] = ''.join(
            str(colouring[e]) for e in enc.edges)
    else:
        record['verdict'] = 'SOLVER_FAILED'
        record['stderr'] = result['stderr'][:400]

    if not keep and os.path.exists(cnf):
        os.remove(cnf)
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('n', type=int)
    ap.add_argument('targets', help='three cycle lengths, e.g. 3,6,6')
    ap.add_argument('--kissat')
    ap.add_argument('--timeout', type=float)
    ap.add_argument('--keep-cnf', action='store_true')
    ap.add_argument('--symmetry', action='store_true',
                    help='add the sorted-star break (satisfiability-preserving)')
    ap.add_argument('--save', action='store_true',
                    help='write the evidence JSON')
    args = ap.parse_args()

    targets = tuple(int(x) for x in args.targets.split(','))
    record = solve(args.n, targets, kissat=args.kissat, timeout=args.timeout,
                   keep=args.keep_cnf, break_symmetry=args.symmetry)
    print(json.dumps(record, indent=1))
    if args.save:
        os.makedirs(EVIDENCE, exist_ok=True)
        suffix = '_sb' if args.symmetry else ''
        name = f'{targets[0]}-{targets[1]}-{targets[2]}_n{args.n}{suffix}.json'
        with open(os.path.join(EVIDENCE, name), 'w', encoding='ascii',
                  newline='\n') as fh:
            json.dump(record, fh, indent=1)
            fh.write('\n')
        print('saved', name)


if __name__ == '__main__':
    main()
